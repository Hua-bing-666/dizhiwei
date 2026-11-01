param([string]$Workspace='C:\Users\Lenovo\Desktop\大创想法')
$ErrorActionPreference='Stop'
$app=New-Object -ComObject kwps.Application
$priorCount=$app.Documents.Count;$priorVisible=$app.Visible;$priorAlerts=$app.DisplayAlerts
if ($priorCount -eq 0){$app.Visible=$false};$app.DisplayAlerts=0
try {
    $doc=$app.Documents.Open((Join-Path $Workspace 'tmp\quality_book\实施项目书.docx'),$false,$false)
    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    $doc.Save()
    $doc.ExportAsFixedFormat((Join-Path $Workspace 'tmp\quality_book\实施项目书.pdf'),17)
    $rowPages=@()
    foreach ($table in $doc.Tables) {
        foreach ($row in $table.Rows) {
            $start=$row.Range.Duplicate;$start.Collapse(1)
            $end=$row.Range.Duplicate;$end.End=$end.End-1;$end.Collapse(0)
            $rowPages+=@{start_page=$start.Information(3);end_page=$end.Information(3);text=$row.Range.Text}
        }
    }
    $paragraphPages=@()
    foreach ($paragraph in $doc.Paragraphs) {
        $value=$paragraph.Range.Text.Trim([char[]]@(13,7,11,32))
        if (-not $value){continue}
        $start=$paragraph.Range.Duplicate;$start.Collapse(1)
        $end=$paragraph.Range.Duplicate;$end.End=$end.End-1;$end.Collapse(0)
        $paragraphPages+=@{text=$value;start_page=$start.Information(3);end_page=$end.Information(3)}
    }
    $figurePages=@()
    foreach ($shape in $doc.InlineShapes) {
        $range=$shape.Range.Paragraphs.Item(1).Range.Duplicate
        $start=$range.Duplicate;$start.Collapse(1)
        $end=$range.Duplicate;$end.End=$end.End-1;$end.Collapse(0)
        $figurePages+=@{caption=$range.Text.Trim([char[]]@(13,7,11,32,1));start_page=$start.Information(3);end_page=$end.Information(3);width_pt=$shape.Width;height_pt=$shape.Height}
    }
    @{pages=$doc.ComputeStatistics(2);source='native WPS';physical_validation=$false;table_rows=$rowPages;paragraphs=$paragraphPages;figures=$figurePages} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Workspace 'tmp\quality_book\native_layout.json') -Encoding utf8NoBOM
    Write-Output ('Execution book native pages='+$doc.ComputeStatistics(2))
    $doc.Close(0)
} finally {
    $app.DisplayAlerts=$priorAlerts
    if ($priorCount -eq 0){$app.Quit()} else {$app.Visible=$priorVisible}
}
