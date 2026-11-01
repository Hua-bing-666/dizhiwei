param([string]$Workspace='C:\Users\Lenovo\Desktop\大创想法')
$ErrorActionPreference='Stop'
$app=New-Object -ComObject kwps.Application
$priorCount=$app.Documents.Count;$priorVisible=$app.Visible;$priorAlerts=$app.DisplayAlerts
if ($priorCount -eq 0){$app.Visible=$false};$app.DisplayAlerts=0
$doc=$null
try {
    $doc=$app.Documents.Open((Join-Path $Workspace 'deliverables\大创申报书_公式与插图修订稿.docx'),$false,$false)
    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    $nativeEquations=$null;$mathApiDiagnostic=$null
    try {$nativeEquations=$doc.OMaths.Count} catch {$mathApiDiagnostic=$_.Exception.Message}
    $doc.Save()
    $doc.ExportAsFixedFormat((Join-Path $Workspace 'deliverables\大创申报书_公式与插图审阅版.pdf'),17)
    $paragraphPages=@()
    foreach ($paragraph in $doc.Paragraphs) {
        $value=$paragraph.Range.Text.Trim([char[]]@(13,7,11,32))
        if (-not $value){continue}
        $start=$paragraph.Range.Duplicate;$start.Collapse(1)
        $end=$paragraph.Range.Duplicate;$end.End=$end.End-1;$end.Collapse(0)
        $paragraphPages+=@{text=$value;start_page=$start.Information(3);end_page=$end.Information(3)}
    }
    @{pages=$doc.ComputeStatistics(2);source='native WPS';physical_validation=$false;native_math_count=$nativeEquations;math_api_diagnostic=$mathApiDiagnostic;paragraphs=$paragraphPages} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Workspace 'tmp\equation_figure_review\native_layout.json') -Encoding utf8NoBOM
    Write-Output ('Native pages='+$doc.ComputeStatistics(2)+'; native equation API count='+$nativeEquations)
} finally {
    if ($null -ne $doc){$doc.Close(0)}
    $app.DisplayAlerts=$priorAlerts
    if ($priorCount -eq 0){$app.Quit()} else {$app.Visible=$priorVisible}
}
