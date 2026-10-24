$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes
$payload=[Console]::ReadLine()
if ($payload.Length -gt 262144) {throw 'payload exceeds bound'}
$p=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload))|ConvertFrom-Json
$root=[Windows.Automation.AutomationElement]::RootElement
function Describe($e, $includeText=$true) {
 $parent=[Windows.Automation.TreeWalker]::ControlViewWalker.GetParent($e)
 $parentId=$null
 if ($null -ne $parent) {$parentId=(@($parent.GetRuntimeId()) -join '.')}
 $text=$null; $v=$null
 if ($includeText -and -not $e.Current.IsPassword -and
     $e.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$v)) {
  $text=$v.Current.Value
 }
 else {
  $t=$null
  if ($includeText -and -not $e.Current.IsPassword -and
      $e.TryGetCurrentPattern([Windows.Automation.TextPattern]::Pattern,[ref]$t)) {
   $text=$t.DocumentRange.GetText(8192)
  }
 }
 @{runtime_id=(@($e.GetRuntimeId()) -join '.');parent_runtime_id=$parentId;name=$e.Current.Name
   type=$e.Current.ControlType.ProgrammaticName; automation_id=$e.Current.AutomationId
   pid=$e.Current.ProcessId;handle=$e.Current.NativeWindowHandle
   enabled=$e.Current.IsEnabled;password=$e.Current.IsPassword;text=$text;
   offscreen=$e.Current.IsOffscreen;
   patterns=@($e.GetSupportedPatterns()|ForEach-Object {$_.ProgrammaticName})}
}
if ($p.operation -eq 'windows') {
 $all=$root.FindAll([Windows.Automation.TreeScope]::Children,[Windows.Automation.Condition]::TrueCondition)
 $result=@(); for ($i=0;$i -lt [Math]::Min($all.Count,100);$i++) { $result+=Describe $all[$i] }
 ConvertTo-Json -InputObject @($result) -Compress -Depth 6; exit
}
if ($p.operation -eq 'focused') {
 Describe ([Windows.Automation.AutomationElement]::FocusedElement) |
  ConvertTo-Json -Compress -Depth 6;exit
}
if ($p.operation -eq 'focused_identity') {
 $e=[Windows.Automation.AutomationElement]::FocusedElement
 @{pid=$e.Current.ProcessId;runtime_id=(@($e.GetRuntimeId()) -join '.');
   password=$e.Current.IsPassword}|ConvertTo-Json -Compress;exit
}
if ($p.operation -eq 'clipboard_write') {
 Add-Type -AssemblyName System.Windows.Forms
 [Windows.Forms.Clipboard]::SetText($p.text)
 @{status='REPORTED'}|ConvertTo-Json -Compress;exit
}
if ($p.operation -eq 'clipboard_read') {
 Add-Type -AssemblyName System.Windows.Forms
 @{text=[Windows.Forms.Clipboard]::GetText()}|ConvertTo-Json -Compress;exit
}
$window=[Windows.Automation.AutomationElement]::FromHandle([IntPtr]$p.handle)
if ($null -eq $window -or $window.Current.ProcessId -ne $p.pid) { throw 'target identity changed' }
if ($p.operation -in @('screenshot','visual_click')) {
 & (Join-Path $PSScriptRoot 'windows_visual.ps1') -Request $p
 exit
}
if ($p.operation -eq 'tree') {
 $queue=[Collections.Generic.Queue[object]]::new();$queue.Enqueue(@{e=$window;depth=0});$result=@()
 $walker=[Windows.Automation.TreeWalker]::ControlViewWalker
 while ($queue.Count -gt 0 -and $result.Count -lt 200) {
  $item=$queue.Dequeue();$result+=Describe $item.e
  if ($item.depth -lt 8) {
   $child=$walker.GetFirstChild($item.e);$count=0
   while ($null -ne $child -and $count -lt 100) {
    $queue.Enqueue(@{e=$child;depth=$item.depth+1});$count++;$child=$walker.GetNextSibling($child)
   }
  }
 }
 ConvertTo-Json -InputObject @($result) -Compress -Depth 6;exit
}
if ($p.operation -eq 'close') {
 $pattern=$null
 if (-not $window.TryGetCurrentPattern(
  [Windows.Automation.WindowPattern]::Pattern,[ref]$pattern)) { throw 'no window pattern' }
 $pattern.Close(); @{operation='close';status='REPORTED'}|ConvertTo-Json -Compress;exit
}
$element=$null
$queue=[Collections.Generic.Queue[object]]::new();$queue.Enqueue(@{e=$window;depth=0})
$walker=[Windows.Automation.TreeWalker]::ControlViewWalker;$visited=0
while ($queue.Count -gt 0 -and $visited++ -lt 500) {
 $item=$queue.Dequeue()
 if ((@($item.e.GetRuntimeId()) -join '.') -eq $p.runtime_id) {$element=$item.e;break}
 if ($item.depth -lt 8) {
  $child=$walker.GetFirstChild($item.e);$count=0
  while ($null -ne $child -and $count++ -lt 100 -and $queue.Count -lt 500) {
   $queue.Enqueue(@{e=$child;depth=$item.depth+1});$child=$walker.GetNextSibling($child)
  }
 }
}
if ($null -eq $element -or $element.Current.ProcessId -ne $p.pid -or $element.Current.IsPassword) {
 throw 'target unavailable/unsafe'
}
switch ($p.operation) {
 'context' {
  if ($element.Current.IsOffscreen -or -not $element.Current.IsEnabled) {throw 'hidden context'}
  $selected=$null; $start=$null; $t=$null
  $description=Describe $element $p.include_current
  if ($element.TryGetCurrentPattern([Windows.Automation.TextPattern]::Pattern,[ref]$t)) {
   $ranges=$t.GetSelection()
   if ($ranges.Count -eq 1) {
    $selected=$ranges[0].GetText(8193)
    if ($p.include_current) {
     $prefix=$t.DocumentRange.Clone()
     $prefix.MoveEndpointByRange([Windows.Automation.Text.TextPatternRangeEndpoint]::End,
      $ranges[0],[Windows.Automation.Text.TextPatternRangeEndpoint]::Start)
     $start=$prefix.GetText(8193).Length
    }
   }
  }
  @{element=$description;selected=$selected;start=$start}|ConvertTo-Json -Compress -Depth 6
 }
 'set_text_checked' {
  $pattern=$null
  if (-not $element.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$pattern) -or
      $pattern.Current.IsReadOnly -or $pattern.Current.Value -cne $p.expected_text) {
   throw 'destination changed or reliable insertion unsupported'
  }
  $pattern.SetValue($p.text)
  @{status='REPORTED';operation='set_text_checked'}|ConvertTo-Json -Compress
 }
 'read' { Describe $element |ConvertTo-Json -Compress -Depth 6 }
 'focus_snapshot' {
  $beforeWindow=Describe $window;$beforeEditor=Describe $element
  $focused=[Windows.Automation.AutomationElement]::FocusedElement
  $focus=@{pid=0;handle=0;runtime_id=$null}
  if ($null -ne $focused) {
   $focus=@{pid=$focused.Current.ProcessId;handle=$focused.Current.NativeWindowHandle;
    runtime_id=(@($focused.GetRuntimeId()) -join '.')}
  }
  @{windows=@($beforeWindow,(Describe $window));
    editors=@($beforeEditor,(Describe $element));focused=$focus} |
   ConvertTo-Json -Compress -Depth 6
 }
 'focus' {
  $element.SetFocus()
  Describe ([Windows.Automation.AutomationElement]::FocusedElement) |
   ConvertTo-Json -Compress -Depth 6
 }
 'invoke' {
  $pattern=$null
  if (-not $element.TryGetCurrentPattern(
   [Windows.Automation.InvokePattern]::Pattern,[ref]$pattern)) {throw 'invoke unsupported'}
  $pattern.Invoke();@{status='REPORTED'}|ConvertTo-Json -Compress
 }
 'select' {
  $pattern=$null
  if (-not $element.TryGetCurrentPattern(
    [Windows.Automation.SelectionItemPattern]::Pattern,[ref]$pattern)) {throw 'select unsupported'}
  $pattern.Select();@{status='REPORTED';operation='select'}|ConvertTo-Json -Compress
 }
 'key' {
  Add-Type -AssemblyName System.Windows.Forms
  $element.SetFocus()
  $focused=[Windows.Automation.AutomationElement]::FocusedElement
  if ($focused.Current.ProcessId -ne $p.pid -or
      (@($focused.GetRuntimeId()) -join '.') -ne $p.runtime_id) {throw 'focus changed'}
  $keys=@{select_all='^a';backspace='{BACKSPACE}';enter='{ENTER}';escape='{ESC}';tab='{TAB}'}
  [Windows.Forms.SendKeys]::SendWait($keys[$p.key])
  @{status='REPORTED';operation='key'}|ConvertTo-Json -Compress
 }
 'close_tab' {
  if ($window.Current.Name -ne $p.expected_title) {throw 'active tab title changed'}
  $element.SetFocus()
  $focused=[Windows.Automation.AutomationElement]::FocusedElement
  if ($focused.Current.ProcessId -ne $p.pid -or
      (@($focused.GetRuntimeId()) -join '.') -ne $p.runtime_id) {throw 'focus changed'}
  Add-Type -AssemblyName System.Windows.Forms
  [Windows.Forms.SendKeys]::SendWait('^w')
  @{status='REPORTED';operation='close_tab'}|ConvertTo-Json -Compress
 }
 'mouse_click' {
  if ($element.Current.IsOffscreen) {throw 'offscreen mouse target'}
  $rect=$element.Current.BoundingRectangle
  if ($rect.Width -le 0 -or $rect.Height -le 0 -or
      $rect.Width -gt 50000 -or $rect.Height -gt 50000) {throw 'invalid bounded rectangle'}
  $element.SetFocus()
  if ([Windows.Automation.AutomationElement]::FocusedElement.Current.ProcessId -ne $p.pid) {
   throw 'target process not focused'
  }
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class OscarPointer {
 [StructLayout(LayoutKind.Sequential)] public struct Mouse {
  public int dx,dy; public uint data,flags,time; public UIntPtr extra;
 }
 [StructLayout(LayoutKind.Sequential)] public struct Input {public uint type;public Mouse mouse;}
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll",SetLastError=true)]
 public static extern uint SendInput(uint count,Input[] input,int size);
 public static bool Click() {
  var a=new Input[2]; a[0].mouse.flags=2; a[1].mouse.flags=4;
  return SendInput(2,a,Marshal.SizeOf(typeof(Input)))==2;
 }
}
'@
  $x=[int]($rect.X+$rect.Width*$p.x_fraction);$y=[int]($rect.Y+$rect.Height*$p.y_fraction)
  if ([Math]::Abs($x) -gt 32767 -or [Math]::Abs($y) -gt 32767) {throw 'coordinate bound'}
  if (-not [OscarPointer]::SetCursorPos($x,$y) -or -not [OscarPointer]::Click()) {
   throw 'input rejected by Windows'
  }
  @{status='REPORTED';operation='mouse_click';x=$x;y=$y}|ConvertTo-Json -Compress
 }
 'set_text' {
  $pattern=$null
  if ($element.TryGetCurrentPattern([Windows.Automation.ValuePattern]::Pattern,[ref]$pattern)) {
   if ($pattern.Current.IsReadOnly) {throw 'read-only target'}; $pattern.SetValue($p.text)
  } else {
   if ($element.Current.ControlType.ProgrammaticName -notin @(
    'ControlType.Edit','ControlType.Document')) {throw 'text fallback requires editor'}
   Add-Type -AssemblyName System.Windows.Forms
   $element.SetFocus()
   $focused=[Windows.Automation.AutomationElement]::FocusedElement
   if ($focused.Current.ProcessId -ne $p.pid -or
    (@($focused.GetRuntimeId()) -join '.') -ne $p.runtime_id) {throw 'focus not verified'}
   $escaped=''; foreach ($c in $p.text.ToCharArray()) {
    if ('+^%~()[]{}'.Contains([string]$c)) { $escaped+='{'+$c+'}' } else {$escaped+=$c}
   }
   [Windows.Forms.SendKeys]::SendWait('^a{BACKSPACE}')
   if ($escaped.Length -gt 0) {[Windows.Forms.SendKeys]::SendWait($escaped)}
  }
  @{status='REPORTED';operation='set_text'}|ConvertTo-Json -Compress
 }
 default {throw 'unsupported typed desktop operation'}
}
