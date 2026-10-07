param([string]$Workspace='C:\Users\Lenovo\Desktop\大创想法')
$ErrorActionPreference='Stop'
$app=New-Object -ComObject kwps.Application
$priorCount=$app.Documents.Count;$priorVisible=$app.Visible;$priorAlerts=$app.DisplayAlerts
if($priorCount -eq 0){$app.Visible=$false};$app.DisplayAlerts=0
$doc=$null
try {
 foreach($item in @(@{file='大创申报书_图文精修稿.docx';folder='submission'},@{file='实施项目书_现阶段更新稿.docx';folder='execution'})){
  $output=Join-Path $Workspace ('tmp\usability_submission\'+$item.folder)
  New-Item -ItemType Directory -Path $output -Force | Out-Null
  $doc=$app.Documents.Open((Join-Path $Workspace ('deliverables\'+$item.file)),$false,$true)
  $doc.Repaginate();$mathCount=$doc.OMaths.Count
  $doc.ExportAsFixedFormat((Join-Path $output 'document.pdf'),17)
  $paragraphs=@();$figures=@();$tables=@()
  foreach($p in $doc.Paragraphs){
   $value=$p.Range.Text.Trim([char[]]@(13,7,11,32));if(-not $value){continue}
   $start=$p.Range.Duplicate;$start.Collapse(1);$end=$p.Range.Duplicate;$end.End=$end.End-1;$end.Collapse(0)
   $paragraphs+=@{text=$value;start_page=$start.Information(3);end_page=$end.Information(3)}
  }
  foreach($shape in $doc.InlineShapes){
   $range=$shape.Range.Paragraphs.Item(1).Range.Duplicate;$start=$range.Duplicate;$start.Collapse(1);$end=$range.Duplicate;$end.End=$end.End-1;$end.Collapse(0)
   $figures+=@{caption=$range.Text.Trim([char[]]@(13,7,11,32,1));start_page=$start.Information(3);end_page=$end.Information(3);width_pt=$shape.Width;height_pt=$shape.Height}
  }
  foreach($table in $doc.Tables){
   if($table.Range.Text.Length -gt 4000){continue}
   $range=$table.Range.Duplicate;$start=$range.Duplicate;$start.Collapse(1);$end=$range.Duplicate;$end.End=$end.End-1;$end.Collapse(0)
   $tables+=@{text=$range.Text;start_page=$start.Information(3);end_page=$end.Information(3)}
  }
  @{source=$item.file;renderer='native WPS';pages=$doc.ComputeStatistics(2);math_count=$mathCount;paragraphs=$paragraphs;figures=$figures;tables=$tables} | ConvertTo-Json -Depth 7 | Set-Content (Join-Path $output 'native_layout.json') -Encoding utf8NoBOM
  Write-Output ($item.file+' pages='+$doc.ComputeStatistics(2)+' native_math='+$mathCount)
  $doc.Close(0);$doc=$null
 }
} finally {
 if($null -ne $doc){$doc.Close(0)}
 $app.DisplayAlerts=$priorAlerts
 if($priorCount -eq 0){$app.Quit()}else{$app.Visible=$priorVisible}
}
