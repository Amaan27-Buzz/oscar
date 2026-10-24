param([Parameter(Mandatory=$true)][object]$Request)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
public static class OscarSelectedWindow {
 [StructLayout(LayoutKind.Sequential)] public struct Rect {public int left,top,right,bottom;}
 [StructLayout(LayoutKind.Sequential)] public struct Point {public int x,y;}
 [StructLayout(LayoutKind.Sequential)] public struct Mouse {
  public int x,y; public uint data,flags,time; public UIntPtr extra;
 }
 [StructLayout(LayoutKind.Sequential)] public struct Input {public uint type; public Mouse mouse;}
 [DllImport("user32.dll")] static extern bool GetClientRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
 [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr h,IntPtr dc,uint flags);
 [DllImport("user32.dll")] static extern bool ClientToScreen(IntPtr h,ref Point p);
 [DllImport("user32.dll")] static extern IntPtr WindowFromPoint(Point p);
 [DllImport("user32.dll")] static extern IntPtr GetAncestor(IntPtr h,uint flag);
 [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] static extern bool SetCursorPos(int x,int y);
 [DllImport("user32.dll")] static extern uint SendInput(uint n,Input[] i,int size);
 [DllImport("user32.dll")] static extern short GetAsyncKeyState(int key);
 [DllImport("user32.dll")] static extern IntPtr SetThreadDpiAwarenessContext(IntPtr context);
 public sealed class Frame {
  public int width,height; public byte[] bytes; public string sha256;
 }
 static void Target(IntPtr h,uint pid) {
  uint actual; GetWindowThreadProcessId(h,out actual);
  if(actual!=pid || !IsWindowVisible(h) || IsIconic(h) || GetAncestor(h,2)!=h)
   throw new InvalidOperationException("Selected visible window identity changed");
 }
 public static Frame Capture(IntPtr h,uint pid) {
  IntPtr previous=SetThreadDpiAwarenessContext(new IntPtr(-4));
  try {
   Target(h,pid); Rect r;
   if(!GetClientRect(h,out r) || r.right<1 || r.bottom<1 || r.right>4096 || r.bottom>2160)
    throw new InvalidOperationException("Selected window dimensions unavailable");
   using(var bitmap=new Bitmap(r.right,r.bottom,PixelFormat.Format24bppRgb)) {
    using(var graphics=Graphics.FromImage(bitmap)) {
     IntPtr dc=graphics.GetHdc();
     // shortcut: app-rendered pixels; add OS capture for unsupported GPU windows.
     try {if(!PrintWindow(h,dc,1)) throw new InvalidOperationException("Window rendering unavailable");}
     finally {graphics.ReleaseHdc(dc);}
    }
    Target(h,pid); Rect after;
    if(!GetClientRect(h,out after) || after.right!=r.right || after.bottom!=r.bottom)
     throw new InvalidOperationException("Selected window resized during capture");
    using(var stream=new MemoryStream()) {
     bitmap.Save(stream,ImageFormat.Png);
     if(stream.Length>1000000) throw new InvalidOperationException("Window frame exceeds bound");
     byte[] bytes=stream.ToArray();
     using(var hash=SHA256.Create()) return new Frame {width=r.right,height=r.bottom,bytes=bytes,
      sha256=BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-","").ToLowerInvariant()};
    }
   }
  } finally {SetThreadDpiAwarenessContext(previous);}
 }
 public static void Click(IntPtr h,uint pid,int width,int height,string hash,int x,int y) {
  IntPtr previous=SetThreadDpiAwarenessContext(new IntPtr(-4));
  try {
   Target(h,pid);
   if(GetForegroundWindow()!=h) throw new InvalidOperationException("Selected window is not foreground");
   Frame frame=Capture(h,pid);
   if(frame.width!=width || frame.height!=height || frame.sha256!=hash || x<0 || y<0 || x>=width || y>=height)
    throw new InvalidOperationException("Reviewed frame changed");
   Point point=new Point {x=x,y=y};
   if(!ClientToScreen(h,ref point) || GetAncestor(WindowFromPoint(point),2)!=h)
    throw new InvalidOperationException("Selected point is obstructed");
   if(!SetCursorPos(point.x,point.y)) throw new InvalidOperationException("Pointer unavailable");
   Target(h,pid);
   if(GetForegroundWindow()!=h || GetAncestor(WindowFromPoint(point),2)!=h)
    throw new InvalidOperationException("Input target changed");
   foreach(int key in new int[] {1,2,16,17,18,91,92})
    if((GetAsyncKeyState(key)&0x8000)!=0)
     throw new InvalidOperationException("Existing input must be released before visual input");
   var inputs=new Input[2]; inputs[0].mouse.flags=2; inputs[1].mouse.flags=4;
   if(SendInput(2,inputs,Marshal.SizeOf(typeof(Input)))!=2)
    throw new InvalidOperationException("Input unavailable or incomplete; do not replay");
  } finally {SetThreadDpiAwarenessContext(previous);}
 }
}
'@
if ($Request.operation -eq 'screenshot') {
 $frame=[OscarSelectedWindow]::Capture([IntPtr]$Request.handle,[uint32]$Request.pid)
 @{width=$frame.width;height=$frame.height;sha256=$frame.sha256;
   png=[Convert]::ToBase64String($frame.bytes)}|ConvertTo-Json -Compress
} elseif ($Request.operation -eq 'visual_click') {
 [OscarSelectedWindow]::Click([IntPtr]$Request.handle,[uint32]$Request.pid,
  $Request.width,$Request.height,$Request.sha256,$Request.x,$Request.y)
 @{status='REPORTED';operation='visual_click'}|ConvertTo-Json -Compress
} else {throw 'Unsupported selected-window operation'}
