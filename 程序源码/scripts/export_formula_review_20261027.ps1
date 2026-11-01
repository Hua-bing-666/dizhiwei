param([Parameter(Mandatory=$true)][string]$InputDocument,[Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference='Stop'
$inputPath=(Resolve-Path -LiteralPath $InputDocument).Path
$outputPath=[IO.Path]::GetFullPath($OutputPdf)
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($outputPath)) | Out-Null
$app=New-Object -ComObject kwps.Application
$priorCount=$app.Documents.Count
$priorVisible=$app.Visible
$priorAlerts=$app.DisplayAlerts
$doc=$null
try {
 if ($priorCount -eq 0) { $app.Visible=$false }
 $app.DisplayAlerts=0
 $doc=$app.Documents.Open($inputPath,$false,$true)
 $doc.Repaginate()
 $doc.ExportAsFixedFormat($outputPath,17)
 $record=@{pages=$doc.ComputeStatistics(2);renderer='WPS read-only native PDF export';input=$inputPath;output=$outputPath;sourceSaved=$false}
 try { $record.nativeEquations=$doc.OMaths.Count } catch { $record.mathApiUnavailable=$true }
 $record | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath ($outputPath+'.json') -Encoding UTF8
 $record | ConvertTo-Json -Compress
} finally {
 if ($null -ne $doc) { $doc.Close(0) }
 $app.DisplayAlerts=$priorAlerts
 if ($priorCount -eq 0) { $app.Quit() } else { $app.Visible=$priorVisible }
}
