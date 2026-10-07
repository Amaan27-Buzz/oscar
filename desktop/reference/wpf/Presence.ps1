param([int]$HotkeyModifiers=3,[int]$HotkeyKey=79,[switch]$SelfCheck,[string]$OutputDirectory)
$ErrorActionPreference='Stop'
function Reference-Stage($name) {if ($SelfCheck) {[Console]::Error.WriteLine('desktop.reference.stage='+$name)}}
Reference-Stage 'bootstrap'
Add-Type -AssemblyName PresentationFramework,PresentationCore,WindowsBase,System.Windows.Forms,System.Drawing,System.Net.Http
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class OscarHotkey {
 [DllImport("user32.dll", SetLastError=true)] public static extern bool RegisterHotKey(IntPtr h,int id,uint mods,uint key);
 [DllImport("user32.dll")] public static extern bool UnregisterHotKey(IntPtr h,int id);
 [DllImport("user32.dll")] public static extern bool DestroyIcon(IntPtr h);
}
'@
# Trusted composition passes ephemeral credentials by inherited stdin, never argv/files/logs.
$bootstrap=[Console]::ReadLine()|ConvertFrom-Json
if ($bootstrap.url -notmatch '^http://127\.0\.0\.1:[0-9]+$') {throw 'Loopback Core required'}
$key=[Security.Cryptography.CngKey]::Import([Convert]::FromBase64String($bootstrap.pkcs8),[Security.Cryptography.CngKeyBlobFormat]::Pkcs8PrivateBlob)
$rsa=[Security.Cryptography.RSACng]::new($key)
Reference-Stage 'cng'
$client=[Net.Http.HttpClient]::new()
$client.Timeout=[TimeSpan]::FromSeconds(130)
$client.DefaultRequestHeaders.Authorization=[Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer',$bootstrap.token)
$client.DefaultRequestHeaders.Add('X-Oscar-Node',$bootstrap.node)
$client.DefaultRequestHeaders.Add('X-Oscar-Session',$bootstrap.session)
$bootstrap.pkcs8=$null;$bootstrap.token=$null
[xml]$xaml=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Presence.xaml') -Raw
$window=[Windows.Markup.XamlReader]::Load([Xml.XmlNodeReader]::new($xaml))
Reference-Stage 'xaml'
$ui=@{}; @('Orb','State','Expand','Body','Boundary','Mode','CaptureSource','Discard','Context','ActFields','ActPath','Input','Submit','Voice','Result','Tasks','Approve','Cancel','Preview','PreviewText','ApplyControls','Destination','Apply','Shortcut')|ForEach-Object {$ui[$_]=$window.FindName($_)}
$ui.Orb.Source=[Windows.Media.Imaging.BitmapImage]::new([Uri]$bootstrap.orb)
$ui.Boundary.Text=$bootstrap.boundary
$script:pending=[Collections.Generic.List[object]]::new()
$script:taskId=$null;$script:contextId='';$script:previewId=$null;$script:busy=$false
$script:voiceActive=$false
function Send-Core($operation,$payload,$callback) {
 $body=@{version=1;operation=$operation;request_id=[Guid]::NewGuid().ToString('N');payload=$payload}|ConvertTo-Json -Depth 20 -Compress
 $content=[Net.Http.StringContent]::new($body,[Text.Encoding]::UTF8,'application/json')
 $task=$client.PostAsync($bootstrap.url+'/v1/desktop',$content)
 $script:pending.Add(@{task=$task;callback=$callback;content=$content;operation=$operation})
}
function Expand-Presence {
 $ui.Body.Visibility='Visible';$window.Height=720;$ui.Expand.Content='Collapse'
 $window.Show();$window.Activate()|Out-Null;$ui.Input.Focus()|Out-Null
}
function Invoke-Presence {
 $source=[string]$ui.CaptureSource.SelectedItem.Tag
 if ($source) {
  # Capture occurs before activating OSCAR, and only for the explicitly chosen source.
  Send-Core 'capture' @{source=$source} {
   param($view)
   $script:contextId=$view.id
   $ui.Context.Text=$view.source+' | '+$view.freshness+' | '+$view.permission+': '+$view.text
   Expand-Presence
  }
 } else {Expand-Presence}
}
function Show-View($view) {
 if ($view.task_id) {$script:taskId=$view.task_id}
 $ui.State.Text=if ($view.state) {$view.state+' | '+$view.orb} else {'Attentive'}
 $ui.Result.Text=if ($view.value) {$view.epistemic+': '+$view.value} elseif ($view.response) {$view.response_status+': '+$view.response} else {$view.message}
 $ui.Approve.IsEnabled=@($view.actions) -contains 'approve'
 $ui.Cancel.IsEnabled=@($view.actions) -contains 'cancel'
 $ui.Preview.IsEnabled=([string]$ui.Mode.SelectedItem.Content -eq 'Edit' -and [bool]$view.response)
 if ($view.preview_id) {
  $script:previewId=$view.preview_id;$ui.PreviewText.Text='Before: '+$view.before+"`nAfter: "+$view.after
  $ui.PreviewText.Visibility='Visible';$ui.ApplyControls.Visibility='Visible'
 }
}
function Review-Task($operation) {
 if (-not $script:taskId) {return}
 Send-Core 'challenge' @{operation=$operation;task_id=$script:taskId} {
  param($challenge)
  $review=@('Operation: '+$challenge.operation,'Target: '+$challenge.target,'Capability: '+$challenge.capability,'Reason: '+$challenge.reason,'Consequence: '+$challenge.consequence,'Policy: '+$challenge.policy_reason,'State: '+$challenge.evidence_state,'Review: '+$challenge.review) -join "`n"
  if ([Windows.MessageBox]::Show($window,$review,'OSCAR owner decision','YesNo','Question') -eq 'Yes') {
   $signature=$rsa.SignData([Convert]::FromBase64String($challenge.signing_payload),[Security.Cryptography.HashAlgorithmName]::SHA256,[Security.Cryptography.RSASignaturePadding]::Pss)
   Send-Core 'complete' @{challenge_id=$challenge.challenge_id;signature=[Convert]::ToBase64String($signature)} {param($view) Show-View $view}
  }
 }
}
$ui.Expand.Add_Click({if ($ui.Body.Visibility -eq 'Visible') {$ui.Body.Visibility='Collapsed';$window.Height=112;$ui.Expand.Content='Open'} else {Expand-Presence}})
$ui.Discard.Add_Click({Send-Core 'discard' @{} {param($v) $script:contextId='';$script:previewId=$null;$ui.Context.Text='No context attached';$ui.PreviewText.Text='';$ui.Result.Text='';$ui.Input.Text='';$ui.ApplyControls.Visibility='Collapsed';$ui.PreviewText.Visibility='Collapsed'}})
$ui.Submit.Add_Click({
 $text=$ui.Input.Text;$mode=[string]$ui.Mode.SelectedItem.Content;$context=$script:contextId
 if ($mode -eq 'Act') {
  $text=@{kind='file_write';parameters=@{path=$ui.ActPath.Text;content=$text};criterion=@{kind='file_exact';path=$ui.ActPath.Text;content=$text}}|ConvertTo-Json -Depth 10 -Compress
  $context=''
 }
 Send-Core 'interact' @{mode=$mode;text=$text;context_id=$context} {param($view) Show-View $view}
})
$ui.Mode.Add_SelectionChanged({$ui.ActFields.Visibility=if ([string]$ui.Mode.SelectedItem.Content -eq 'Act') {'Visible'} else {'Collapsed'}})
$ui.Approve.Add_Click({Review-Task 'approve'})
$ui.Cancel.Add_Click({Review-Task 'cancel'})
$ui.Preview.Add_Click({Send-Core 'preview' @{task_id=$script:taskId} {param($v) Show-View $v}})
$ui.Apply.Add_Click({Send-Core 'apply' @{preview_id=$script:previewId;destination=[string]$ui.Destination.SelectedItem.Tag} {param($v) Show-View $v}})
function Start-Dictation {Send-Core 'voice' @{operation='start';context_id=$script:contextId} {param($v) $script:voiceActive=$v.state -eq 'listening';Show-View $v}}
function Finish-Dictation {Send-Core 'voice' @{operation='stop'} {param($v) Show-View $v}}
$ui.Voice.Add_PreviewMouseLeftButtonDown({$ui.Voice.CaptureMouse()|Out-Null;Start-Dictation})
$ui.Voice.Add_PreviewMouseLeftButtonUp({$ui.Voice.ReleaseMouseCapture();Finish-Dictation})
$ui.Voice.Add_PreviewKeyDown({param($s,$e) if ($e.Key -eq 'Space' -and -not $e.IsRepeat) {$e.Handled=$true;Start-Dictation}})
$ui.Voice.Add_PreviewKeyUp({param($s,$e) if ($e.Key -eq 'Space') {$e.Handled=$true;Finish-Dictation}})
$ui.Tasks.Add_SelectionChanged({if ($ui.Tasks.SelectedItem) {Send-Core 'inspect' @{task_id=$ui.Tasks.SelectedItem.task_id} {param($v) Show-View $v}}})
$script:pollAt=[DateTime]::UtcNow
$timer=[Windows.Threading.DispatcherTimer]::new();$timer.Interval=[TimeSpan]::FromMilliseconds(100)
$timer.Add_Tick({
 foreach ($item in @($script:pending.ToArray())) {
  if (-not $item.task.IsCompleted) {continue}
  try {
   $response=$item.task.GetAwaiter().GetResult()
   $json=$response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
   if (-not $response.IsSuccessStatusCode) {throw 'Core denied/unavailable'}
   $view=$json|ConvertFrom-Json
   & $item.callback $view
   $response.Dispose()
  } catch {$ui.State.Text='Degraded | UNKNOWN';$ui.Result.Text='Core unavailable or request rejected. Inspect before retry.';$ui.Approve.IsEnabled=$false;$ui.Cancel.IsEnabled=$false}
  finally {$item.content.Dispose();$script:pending.Remove($item)|Out-Null}
 }
 if ([DateTime]::UtcNow -ge $script:pollAt) {
  $script:pollAt=[DateTime]::UtcNow.AddSeconds(2)
  if ($script:voiceActive) {Send-Core 'voice' @{operation='inspect'} {param($v) Show-View $v;if ($v.preview_id -or $v.state -eq 'blocked') {$script:voiceActive=$false}}}
  Send-Core 'snapshot' @{} {
   param($view)
   $selected=$script:taskId
   if (-not $selected) {$active=@($view.tasks|Where-Object {$_.state -notin @('verified','failed','cancelled')});if ($active.Count) {$selected=$active[-1].task_id}}
   $ui.Tasks.ItemsSource=@($view.tasks|ForEach-Object {$_|Add-Member -NotePropertyName label -NotePropertyValue ($_.state+' | '+$_.description) -Force -PassThru})
   if ($selected) {Send-Core 'inspect' @{task_id=$selected} {param($v) Show-View $v}}
   elseif (-not $script:previewId) {$ui.State.Text='Idle | Core connected'}
  }
 }
})
Reference-Stage 'tray'
$tray=[Windows.Forms.NotifyIcon]::new()
$orbBitmap=[Drawing.Bitmap]::new($bootstrap.orb);$iconHandle=$orbBitmap.GetHicon()
$trayIcon=[Drawing.Icon]::FromHandle($iconHandle).Clone();$orbBitmap.Dispose()
[OscarHotkey]::DestroyIcon($iconHandle)|Out-Null
$tray.Icon=$trayIcon;$tray.Text='OSCAR';$tray.Visible=$true
$tray.Add_Click({Invoke-Presence})
$window.Add_SourceInitialized({
 $script:handle=[Windows.Interop.WindowInteropHelper]::new($window).Handle
 $script:hwnd=[Windows.Interop.HwndSource]::FromHwnd($script:handle)
 $script:hook=[Windows.Interop.HwndSourceHook]{param($h,$message,$w,$l,[ref]$handled) if ($message -eq 0x312 -and $w.ToInt32() -eq 10) {$handled.Value=$true;Invoke-Presence};return [IntPtr]::Zero}
 $script:hwnd.AddHook($script:hook)
 $script:hotkey=[OscarHotkey]::RegisterHotKey($script:handle,10,($HotkeyModifiers -bor 0x4000),$HotkeyKey)
 $ui.Shortcut.Text=if ($script:hotkey) {'Global invocation registered. Configure modifiers/key in launcher. Capture only on explicit invocation.'} else {'Shortcut collision/unavailable. Use tray or presence. No input hook installed.'}
})
$window.Add_Closed({$timer.Stop();if ($script:hotkey) {[OscarHotkey]::UnregisterHotKey($script:handle,10)|Out-Null};$tray.Dispose();$trayIcon.Dispose();$client.Dispose();$rsa.Dispose();$key.Dispose()})
if ($SelfCheck) {
 Reference-Stage 'ready'
 function Reference-Post($op,$payload) {
  $data=@{version=1;operation=$op;request_id=[Guid]::NewGuid().ToString('N');payload=$payload}|ConvertTo-Json -Depth 20 -Compress
  $content=[Net.Http.StringContent]::new($data,[Text.Encoding]::UTF8,'application/json')
  $response=$client.PostAsync($bootstrap.url+'/v1/desktop',$content).GetAwaiter().GetResult()
  if (-not $response.IsSuccessStatusCode) {throw 'reference Core request failed'}
  $value=$response.Content.ReadAsStringAsync().GetAwaiter().GetResult()|ConvertFrom-Json
  $content.Dispose();$response.Dispose();return $value
 }
 Reference-Stage 'propose'
 $proposed=Reference-Post 'interact' @{mode='Ask';text='2 + 3';context_id=''}
 Reference-Stage 'challenge'
 $challenge=Reference-Post 'challenge' @{operation='approve';task_id=$proposed.task_id}
 $signature=$rsa.SignData([Convert]::FromBase64String($challenge.signing_payload),[Security.Cryptography.HashAlgorithmName]::SHA256,[Security.Cryptography.RSASignaturePadding]::Pss)
 Reference-Stage 'complete'
 $result=Reference-Post 'complete' @{challenge_id=$challenge.challenge_id;signature=[Convert]::ToBase64String($signature)}
 if ($result.state -ne 'verified' -or $result.value -ne '5') {throw 'native signed Core result mismatch'}
 Reference-Stage 'show'
 Expand-Presence
 Show-View $result
 $ui.State.Text='REFERENCE | owner acceptance not run'
 $window.UpdateLayout()
 Reference-Stage 'render'
 $bitmap=[Windows.Media.Imaging.RenderTargetBitmap]::new([int]$window.ActualWidth,[int]$window.ActualHeight,96,96,[Windows.Media.PixelFormats]::Pbgra32)
 $bitmap.Render($window)
 $encoder=[Windows.Media.Imaging.PngBitmapEncoder]::new();$encoder.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($bitmap))
 $file=[IO.File]::Create((Join-Path $OutputDirectory 'presence.png'));$encoder.Save($file);$file.Dispose()
 $window.Close()
 Reference-Stage 'closed'
 [Console]::WriteLine('{"evidence":"REFERENCE_WPF_RENDER","native_cng_signed_core":"VERIFIED","owner_acceptance":"NOT_RUN"}')
} else {$timer.Start();$window.ShowDialog()|Out-Null}
