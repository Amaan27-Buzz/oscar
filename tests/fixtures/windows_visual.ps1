param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName PresentationFramework,PresentationCore,WindowsBase
[Windows.Media.RenderOptions]::ProcessRenderMode=[Windows.Interop.RenderMode]::SoftwareOnly
$window=[Windows.Window]::new()
$window.Title='OSCAR synthetic visual acceptance'
$window.Width=320;$window.Height=200;$window.WindowStyle='None';$window.ResizeMode='NoResize'
$window.Topmost=$true
$canvas=[Windows.Controls.Canvas]::new();$canvas.Background=[Windows.Media.Brushes]::White
$rectangle=[Windows.Shapes.Rectangle]::new();$rectangle.Width=100;$rectangle.Height=70
$rectangle.Fill=[Windows.Media.BrushConverter]::new().ConvertFromString('#13A7E5')
[Windows.Controls.Canvas]::SetLeft($rectangle,80);[Windows.Controls.Canvas]::SetTop($rectangle,50)
$canvas.Children.Add($rectangle)|Out-Null;$window.Content=$canvas
$script:count=0
$canvas.Add_MouseLeftButtonDown({
 $script:count++
 [IO.File]::WriteAllText((Join-Path $Root 'clicks.txt'),$script:count.ToString())
 $rectangle.Fill=[Windows.Media.Brushes]::Green
})
$window.Add_ContentRendered({
 $window.Activate()|Out-Null
 $handle=[Windows.Interop.WindowInteropHelper]::new($window).Handle
 [IO.File]::WriteAllText((Join-Path $Root 'window.txt'),$handle.ToInt64().ToString())
})
$window.ShowDialog()|Out-Null
