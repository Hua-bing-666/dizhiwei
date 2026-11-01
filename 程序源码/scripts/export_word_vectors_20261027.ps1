$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
if ($args.Count -gt 0) { $InputSvg=$args[0]; $OutputStem=$args[1]; $ScratchFolder=$args[2] }
$projectRoot = Split-Path -Parent $PSScriptRoot
$scratchRoot = Join-Path $projectRoot 'tmp/word_vector_20261027'
if ($ScratchFolder) { $scratchRoot=Join-Path $projectRoot ('tmp/'+$ScratchFolder) }
$sourcePath = Join-Path $projectRoot 'deliverables/技术路线图_核心与两翼_20261027.svg'
$svgPath = Join-Path $projectRoot 'deliverables/技术路线图_Word矢量版_20261027.svg'
$emfPath = Join-Path $projectRoot 'deliverables/技术路线图_Word矢量版_20261027.emf'
if ($InputSvg) { $sourcePath=(Resolve-Path -LiteralPath $InputSvg).Path }
if ($OutputStem) { $svgPath=Join-Path $projectRoot ('deliverables/'+$OutputStem+'.svg'); $emfPath=Join-Path $projectRoot ('deliverables/'+$OutputStem+'.emf') }
$vectorData = Get-Content -LiteralPath (Join-Path $scratchRoot 'vector_elements.json') -Raw -Encoding UTF8 | ConvertFrom-Json

Add-Type -ReferencedAssemblies @('System.dll','System.Core.dll','System.Drawing.dll') -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;
using System.Runtime.InteropServices;

public sealed class RouteGlyph {
 public string D; public float X; public float Y; public float Width; public float Height; public int Points;
}
public sealed class RouteVectorCanvas : IDisposable {
 [DllImport("gdi32.dll")] private static extern int GetDeviceCaps(IntPtr dc,int index);
 private Bitmap reference; private Graphics referenceGraphics; private Metafile image; private Graphics g;
 private static string N(float f) { return f.ToString("0.###",CultureInfo.InvariantCulture); }
 private static Brush BrushFor(string value) { return value=="none"?null:new SolidBrush(ColorTranslator.FromHtml(value)); }
 private static Pen PenFor(string value,float width) { if(value=="none"||width<=0)return null; Pen p=new Pen(ColorTranslator.FromHtml(value),width);p.LineJoin=LineJoin.Round;return p; }
 public RouteVectorCanvas(string file,int width,int height,float printWidthMm) {
  reference=new Bitmap(width,height,PixelFormat.Format32bppArgb);referenceGraphics=Graphics.FromImage(reference);
  IntPtr dc=referenceGraphics.GetHdc();
  float deviceDpiX=0,deviceDpiY=0;
  try { deviceDpiX=25.4f*GetDeviceCaps(dc,8)/GetDeviceCaps(dc,4);deviceDpiY=25.4f*GetDeviceCaps(dc,10)/GetDeviceCaps(dc,6);image=new Metafile(file,dc,new RectangleF(0,0,printWidthMm,printWidthMm*height/width),MetafileFrameUnit.Millimeter,EmfType.EmfOnly); }
  finally { referenceGraphics.ReleaseHdc(dc); }
  g=Graphics.FromImage(image);g.PageUnit=GraphicsUnit.Pixel;g.PageScale=1;g.ScaleTransform(printWidthMm*deviceDpiX/25.4f/width,printWidthMm*deviceDpiY/25.4f/width);g.SmoothingMode=SmoothingMode.None;g.PixelOffsetMode=PixelOffsetMode.None;
 }
 private void Paint(GraphicsPath path,string fill,string stroke,float width,string dash=null) {
  using(Brush b=BrushFor(fill)) { if(b!=null)g.FillPath(b,path); }
  using(Pen p=PenFor(stroke,width)) { if(p!=null){if(!String.IsNullOrEmpty(dash)&&dash!="none"){MatchCollection parts=Regex.Matches(dash,@"[\d.]+");float[] pattern=new float[parts.Count];for(int k=0;k<parts.Count;k++)pattern[k]=float.Parse(parts[k].Value,CultureInfo.InvariantCulture)/width;p.DashPattern=pattern;}g.DrawPath(p,path);} }
 }
 public void Rect(float x,float y,float w,float h,float radius,string fill,string stroke,float width) {
  using(GraphicsPath p=new GraphicsPath()) {
   if(radius<=0) p.AddRectangle(new RectangleF(x,y,w,h));
   else { float d=Math.Min(radius*2,Math.Min(w,h));p.AddArc(x,y,d,d,180,90);p.AddArc(x+w-d,y,d,d,270,90);p.AddArc(x+w-d,y+h-d,d,d,0,90);p.AddArc(x,y+h-d,d,d,90,90);p.CloseFigure(); }
   Paint(p,fill,stroke,width);
  }
 }
 public string DrawPath(string d,string fill,string stroke,float width,bool arrow,string dash=null) {
  MatchCollection matches=Regex.Matches(d,@"[A-Za-z]|[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?");
  string[] t=new string[matches.Count];for(int q=0;q<t.Length;q++)t[q]=matches[q].Value;
  int i=0;float x=0,y=0,sx=0,sy=0,dx=0,dy=0;
  using(GraphicsPath p=new GraphicsPath()) {
   while(i<t.Length) {
    string command=t[i++];float a,b,c,e,f,h;
    switch(command) {
     case "M": x=float.Parse(t[i++],CultureInfo.InvariantCulture);y=float.Parse(t[i++],CultureInfo.InvariantCulture);sx=x;sy=y;p.StartFigure();break;
     case "H": a=float.Parse(t[i++],CultureInfo.InvariantCulture);dx=a-x;dy=0;p.AddLine(x,y,a,y);x=a;break;
     case "V": b=float.Parse(t[i++],CultureInfo.InvariantCulture);dx=0;dy=b-y;p.AddLine(x,y,x,b);y=b;break;
     case "L": a=float.Parse(t[i++],CultureInfo.InvariantCulture);b=float.Parse(t[i++],CultureInfo.InvariantCulture);dx=a-x;dy=b-y;p.AddLine(x,y,a,b);x=a;y=b;break;
     case "C": a=float.Parse(t[i++],CultureInfo.InvariantCulture);b=float.Parse(t[i++],CultureInfo.InvariantCulture);c=float.Parse(t[i++],CultureInfo.InvariantCulture);e=float.Parse(t[i++],CultureInfo.InvariantCulture);f=float.Parse(t[i++],CultureInfo.InvariantCulture);h=float.Parse(t[i++],CultureInfo.InvariantCulture);p.AddBezier(x,y,a,b,c,e,f,h);dx=f-c;dy=h-e;x=f;y=h;break;
     case "Z": dx=sx-x;dy=sy-y;x=sx;y=sy;p.CloseFigure();break;
     default: throw new InvalidOperationException("Unsupported path command "+command);
    }
   }
   Paint(p,fill,stroke,width,dash);
  }
  if(!arrow)return null;
  double len=Math.Sqrt(dx*dx+dy*dy);if(len==0)throw new InvalidOperationException("Arrow has no final tangent");
  float ux=(float)(dx/len),uy=(float)(dy/len);
  PointF[] points={new PointF(x-11*ux+5*uy,y-11*uy-5*ux),new PointF(x+ux,y+uy),new PointF(x-11*ux-5*uy,y-11*uy+5*ux)};
  using(Brush b=new SolidBrush(ColorTranslator.FromHtml(stroke)))g.FillPolygon(b,points);
  return "M"+N(points[0].X)+","+N(points[0].Y)+" L"+N(points[1].X)+","+N(points[1].Y)+" L"+N(points[2].X)+","+N(points[2].Y)+" Z";
 }
 public RouteGlyph Text(string value,float size,bool bold,float centerX,float centerY,string fill) {
  using(FontFamily family=new FontFamily("SimSun"))using(GraphicsPath p=new GraphicsPath(FillMode.Alternate)) {
   p.AddString(value,family,(int)(bold?FontStyle.Bold:FontStyle.Regular),size,new PointF(0,0),StringFormat.GenericTypographic);
   RectangleF before=p.GetBounds();using(Matrix move=new Matrix()){move.Translate(centerX-before.X-before.Width/2,centerY-before.Y-before.Height/2);p.Transform(move);}
   Paint(p,fill,"none",0);RectangleF bounds=p.GetBounds();StringBuilder d=new StringBuilder();
   PointF[] points=p.PathPoints;byte[] types=p.PathTypes;
   for(int i=0;i<points.Length;i++) {
    int type=types[i]&7;
    if(type==0)d.Append("M").Append(N(points[i].X)).Append(',').Append(N(points[i].Y));
    else if(type==1)d.Append(" L").Append(N(points[i].X)).Append(',').Append(N(points[i].Y));
    else if(type==3) {
     if(i+2>=points.Length)throw new InvalidOperationException("Incomplete glyph Bezier");
     d.Append(" C").Append(N(points[i].X)).Append(',').Append(N(points[i].Y)).Append(' ').Append(N(points[i+1].X)).Append(',').Append(N(points[i+1].Y)).Append(' ').Append(N(points[i+2].X)).Append(',').Append(N(points[i+2].Y));i+=2;
    } else throw new InvalidOperationException("Unexpected glyph point type");
    if((types[i]&128)!=0)d.Append(" Z");
   }
   return new RouteGlyph{D=d.ToString(),X=bounds.X,Y=bounds.Y,Width=bounds.Width,Height=bounds.Height,Points=points.Length};
  }
 }
 public void Dispose() { if(g!=null){g.Dispose();g=null;}if(image!=null){image.Dispose();image=null;}if(referenceGraphics!=null){referenceGraphics.Dispose();referenceGraphics=null;}if(reference!=null){reference.Dispose();reference=null;} }
}
'@

[xml]$document = Get-Content -LiteralPath $sourcePath -Raw -Encoding UTF8
$svgNamespace = 'http://www.w3.org/2000/svg'
$ns = [Xml.XmlNamespaceManager]::new($document.NameTable)
$ns.AddNamespace('s',$svgNamespace)
$nodes = @($document.SelectNodes('//*[self::s:rect or self::s:path or self::s:text or self::s:line][not(ancestor::s:defs)]',$ns))
if ($nodes.Count -ne $vectorData.elements.Count) { throw 'Source and browser element order differ' }
$canvas = [RouteVectorCanvas]::new($emfPath, [int]$vectorData.width, [int]$vectorData.height, [single]$vectorData.printWidthMm)
$glyphRecords = [Collections.Generic.List[object]]::new()
try {
 foreach ($element in $vectorData.elements) {
  $node = $nodes[[int]$element.index]
  if ($element.tag -eq 'text') {
   $centerX = [single]($element.bbox.x + $element.bbox.width/2)
   $centerY = [single]($element.bbox.y + $element.bbox.height/2)
   $glyph = $canvas.Text($element.text,[single]$element.fontSize,([int]$element.fontWeight -ge 600),$centerX,$centerY,$element.fill)
   $replacement = $document.CreateElement('path',$svgNamespace)
   $replacement.SetAttribute('d',$glyph.D)
   $replacement.SetAttribute('fill',$element.fill)
   $replacement.SetAttribute('fill-rule','evenodd')
   $replacement.SetAttribute('stroke','none')
   $replacement.SetAttribute('font-size',[string]$element.fontSize)
   $replacement.SetAttribute('data-source-text',$element.text)
   $replacement.SetAttribute('aria-label',$element.text)
   [void]$node.ParentNode.ReplaceChild($replacement,$node)
   $glyphRecords.Add([pscustomobject]@{text=$element.text;fontSize=$element.fontSize;points=$glyph.Points;bounds=@($glyph.X,$glyph.Y,$glyph.Width,$glyph.Height);sourceWidth=$element.bbox.width;outlineWidth=$glyph.Width})
   continue
  }
  $node.RemoveAttribute('class')
  $node.SetAttribute('fill',$element.fill)
  $node.SetAttribute('stroke',$element.stroke)
  $node.SetAttribute('stroke-width',[string]$element.strokeWidth)
  if ($element.strokeDash -and $element.strokeDash -ne 'none') { $node.SetAttribute('stroke-dasharray',[string]$element.strokeDash) }
  $node.SetAttribute('stroke-linejoin',$element.lineJoin)
  $node.SetAttribute('stroke-linecap',$element.lineCap)
  $node.RemoveAttribute('marker-end')
  if ($element.tag -eq 'rect') {
   $radius = 0
   if ($null -ne $element.attrs.rx) { $radius = [single]$element.attrs.rx }
   $canvas.Rect([single]$element.attrs.x,[single]$element.attrs.y,[single]$element.attrs.width,[single]$element.attrs.height,[single]$radius,$element.fill,$element.stroke,[single]$element.strokeWidth)
  } elseif ($element.tag -eq 'path') {
   $triangle = $canvas.DrawPath($element.attrs.d,$element.fill,$element.stroke,[single]$element.strokeWidth,[bool]$element.arrow,[string]$element.strokeDash)
   if ($triangle) {
    $arrow = $document.CreateElement('path',$svgNamespace)
    $arrow.SetAttribute('d',$triangle);$arrow.SetAttribute('fill',$element.stroke);$arrow.SetAttribute('stroke','none')
    [void]$node.ParentNode.InsertAfter($arrow,$node)
   }
  } elseif ($element.tag -eq 'line') {
   $lineD = 'M'+$element.attrs.x1+','+$element.attrs.y1+' L'+$element.attrs.x2+','+$element.attrs.y2
   [void]$canvas.DrawPath($lineD,'none',$element.stroke,[single]$element.strokeWidth,$false)
  } else { throw ('Unexpected primitive '+$element.tag) }
 }
} finally { $canvas.Dispose() }

foreach ($definition in @($document.SelectNodes('//s:defs',$ns))) { [void]$definition.ParentNode.RemoveChild($definition) }
$document.DocumentElement.SetAttribute('width',([string]$vectorData.printWidthMm)+'mm')
$physicalHeight = [double]$vectorData.printWidthMm * [double]$vectorData.height / [double]$vectorData.width
$document.DocumentElement.SetAttribute('height',([string]$physicalHeight)+'mm')
$document.DocumentElement.SetAttribute('data-outlined-text','true')
$writerSettings = [Xml.XmlWriterSettings]::new()
$writerSettings.Encoding = [Text.UTF8Encoding]::new($false)
$writerSettings.Indent = $true
$writer = [Xml.XmlWriter]::Create($svgPath,$writerSettings)
try { $document.Save($writer) } finally { $writer.Dispose() }

# Match the physical frame to the recorded device bounds. Windows display scaling
# can otherwise leave unused space around a GDI+ metafile. Word may resize the
# resulting vector image to the recommended 155 mm without raster resampling.
$emfBytes = [IO.File]::ReadAllBytes($emfPath)
$deviceWidth = [BitConverter]::ToInt32($emfBytes,72)
$deviceHeight = [BitConverter]::ToInt32($emfBytes,76)
$deviceWidthMm = [BitConverter]::ToInt32($emfBytes,80)
$deviceHeightMm = [BitConverter]::ToInt32($emfBytes,84)
foreach ($pair in @(@(8,24,$deviceWidthMm,$deviceWidth),@(12,28,$deviceHeightMm,$deviceHeight),@(16,32,$deviceWidthMm,$deviceWidth),@(20,36,$deviceHeightMm,$deviceHeight))) {
 $frameValue = [int][math]::Round([BitConverter]::ToInt32($emfBytes,$pair[0])*100.0*$pair[2]/$pair[3])
 [BitConverter]::GetBytes($frameValue).CopyTo($emfBytes,$pair[1])
}
[IO.File]::WriteAllBytes($emfPath,$emfBytes)

$recordTypes = @{}
$rasterRecords = [Collections.Generic.List[int]]::new()
$rasterTypes = @(76,77,78,79,80,81,114,116)
$position = 0
while ($position + 8 -le $emfBytes.Length) {
 $type = [BitConverter]::ToUInt32($emfBytes,$position)
 $length = [BitConverter]::ToUInt32($emfBytes,$position+4)
 if ($length -lt 8 -or $position+$length -gt $emfBytes.Length) { throw 'Invalid EMF record length' }
 $key = [string]$type
 if (-not $recordTypes.ContainsKey($key)) { $recordTypes[$key] = 0 }
 $recordTypes[$key]++
 if ($rasterTypes -contains $type) { $rasterRecords.Add([int]$type) }
 $position += [int]$length
}
if ($position -ne $emfBytes.Length -or $rasterRecords.Count -ne 0) { throw 'EMF validation failed or raster records detected' }

$previewPath = Join-Path $scratchRoot 'emf_preview.png'
$metafile = [Drawing.Imaging.Metafile]::new($emfPath)
try {
 $preview = [Drawing.Bitmap]::new([int]$vectorData.width*2,[int]$vectorData.height*2)
 try {
  $previewGraphics = [Drawing.Graphics]::FromImage($preview)
  try {
   $previewGraphics.Clear([Drawing.Color]::White)
   $previewGraphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
   $previewGraphics.DrawImage($metafile,[Drawing.Rectangle]::new(0,0,$preview.Width,$preview.Height))
  } finally { $previewGraphics.Dispose() }
  $preview.Save($previewPath,[Drawing.Imaging.ImageFormat]::Png)
 } finally { $preview.Dispose() }
 $metafileType = $metafile.GetMetafileHeader().Type.ToString()
 $metafileDpi = $metafile.HorizontalResolution
} finally { $metafile.Dispose() }

$receipt = [ordered]@{
 source=$sourcePath; outlinedSvg=$svgPath; emf=$emfPath; preview=$previewPath
 printWidthMm=$vectorData.printWidthMm; printHeightMm=$physicalHeight
 outlinedTextCount=$glyphRecords.Count; textNodesRemaining=$document.SelectNodes('//s:text',$ns).Count
 embeddedImages=$document.SelectNodes('//s:image',$ns).Count; emfRasterRecords=$rasterRecords.Count
 metafileType=$metafileType; emfDpi=$metafileDpi; emfRecordTypes=$recordTypes
 emfNativeWidthMm=([BitConverter]::ToInt32($emfBytes,32)-[BitConverter]::ToInt32($emfBytes,24))/100.0
 emfNativeHeightMm=([BitConverter]::ToInt32($emfBytes,36)-[BitConverter]::ToInt32($emfBytes,28))/100.0
 manualVisualReview='pending'; glyphs=$glyphRecords
}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $scratchRoot 'vector_export_receipt.json') -Encoding UTF8
[pscustomobject]@{outlinedTextCount=$glyphRecords.Count;textNodesRemaining=$receipt.textNodesRemaining;embeddedImages=$receipt.embeddedImages;emfRasterRecords=$rasterRecords.Count;metafileType=$metafileType;emfDpi=$metafileDpi;svg=$svgPath;emf=$emfPath} | ConvertTo-Json -Compress
