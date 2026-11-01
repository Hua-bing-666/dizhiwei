param([string]$Workspace='C:\Users\Lenovo\Desktop\大创想法')
$ErrorActionPreference='Stop'
$app=New-Object -ComObject kwps.Application
$priorCount=$app.Documents.Count;$priorVisible=$app.Visible;$priorAlerts=$app.DisplayAlerts
if ($priorCount -eq 0){$app.Visible=$false};$app.DisplayAlerts=0
$doc=$null
try {
    $doc=$app.Documents.Open((Join-Path $Workspace 'deliverables\大创申报书_研究方案收敛稿.docx'),$false,$true)
    $doc.Repaginate()
    $nativeEquations=$doc.OMaths.Count
    $doc.ExportAsFixedFormat((Join-Path $Workspace 'tmp\software_closeout\application.pdf'),17)
    $paragraphPages=@()
    foreach ($paragraph in $doc.Paragraphs) {
        $value=$paragraph.Range.Text.Trim([char[]]@(13,7,11,32))
        if (-not $value){continue}
        $start=$paragraph.Range.Duplicate;$start.Collapse(1)
        $end=$paragraph.Range.Duplicate;$end.End=$end.End-1;$end.Collapse(0)
        $paragraphPages+=@{text=$value;start_page=$start.Information(3);end_page=$end.Information(3)}
    }
    @{pages=$doc.ComputeStatistics(2);source='WPS read-only native export';native_math_count=$nativeEquations;paragraphs=$paragraphPages} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Workspace 'tmp\software_closeout\native_layout.json') -Encoding utf8
    Write-Output ('Native pages='+$doc.ComputeStatistics(2)+'; native equations='+$nativeEquations)
} finally {
    if ($null -ne $doc){$doc.Close(0)}
    $app.DisplayAlerts=$priorAlerts
    if ($priorCount -eq 0){$app.Quit()} else {$app.Visible=$priorVisible}
}
