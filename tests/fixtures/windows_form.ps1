param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName PresentationFramework,PresentationCore,WindowsBase
[xml]$markup=@"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Title="OSCAR synthetic capability acceptance"
 Width="480" Height="200" ShowActivated="False" ShowInTaskbar="False" Focusable="False">
 <StackPanel Margin="20">
  <TextBox x:Name="Input" AutomationProperties.Name="Synthetic input" Focusable="False" IsTabStop="False"/>
  <Button x:Name="Submit" Content="Submit synthetic form" Margin="0,10,0,10" Focusable="False" IsTabStop="False"/>
  <TextBlock x:Name="Result" Text="Waiting"/>
 </StackPanel>
</Window>
"@
$form=[Windows.Markup.XamlReader]::Load([Xml.XmlNodeReader]::new($markup))
$field=$form.FindName('Input')
$result=$form.FindName('Result')
$form.FindName('Submit').Add_Click({
 [IO.File]::WriteAllText((Join-Path $Root 'submitted.txt'),$field.Text,[Text.UTF8Encoding]::new($false))
 $result.Text='Submitted: '+$field.Text
})
$form.Add_ContentRendered({
 $handle=[Windows.Interop.WindowInteropHelper]::new($form).Handle
 [IO.File]::WriteAllText((Join-Path $Root 'keyboard-focus.txt'),$field.IsKeyboardFocused.ToString())
 [IO.File]::WriteAllText((Join-Path $Root 'window.txt'),$handle.ToInt64().ToString())
})
# Keep the fixture off the owner's keyboard path; UIA patterns do not need focus.
$application=[Windows.Application]::new()
$application.Run($form)|Out-Null
