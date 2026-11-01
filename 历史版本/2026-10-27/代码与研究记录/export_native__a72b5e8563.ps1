param([string]$InputDoc,[string]$OutputPdf,[string]$LayoutJson)
$ErrorActionPreference='Stop'
$app=New-Object -ComObject kwps.Application
$count=$app.Documents.Count;$visible=$app.Visible;$alerts=$app.DisplayAlerts
$doc=$null
try {
    if($count -eq 0){$app.Visible=$false}
    $app.DisplayAlerts=0
    $doc=$app.Documents.Open($InputDoc,$false,$true)
    $doc.Repaginate()
    $doc.ExportAsFixedFormat($OutputPdf,17)
    $paragraphs=@()
    foreach($p in $doc.Paragraphs){
        $text=$p.Range.Text.Trim([char[]]@(13,7,11,32))
        if(-not $text){continue}
        $r=$p.Range.Duplicate;$r.Collapse(1)
        $last=$p.Range.Duplicate;$last.End=$last.End-1;$last.Collapse(0)
        $paragraphs+=@{text=$text;start_page=$r.Information(3);end_page=$last.Information(3)}
    }
    @{pages=$doc.ComputeStatistics(2);paragraphs=$paragraphs;renderer='Native WPS read-only export; bundled LibreOffice unavailable on Windows'} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $LayoutJson -Encoding utf8
    Write-Output ('Rendered '+$doc.ComputeStatistics(2)+' pages')
}finally{
    if($null -ne $doc){$doc.Close(0)}
    $app.DisplayAlerts=$alerts
    if($count -eq 0){$app.Quit()}else{$app.Visible=$visible}
}
