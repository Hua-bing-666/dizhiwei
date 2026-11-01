param([string]$Workspace = 'C:\Users\Lenovo\Desktop\大创想法', [string]$OutputDirectory = 'tmp\application_integration\candidate')
$ErrorActionPreference = 'Stop'
$payload = Get-Content -LiteralPath (Join-Path $Workspace 'tmp\reference_review\application_payload.json') -Raw | ConvertFrom-Json
$app = New-Object -ComObject kwps.Application
$priorDocumentCount=$app.Documents.Count
$priorVisible=$app.Visible
$priorAlerts=$app.DisplayAlerts
if ($priorDocumentCount -eq 0) {$app.Visible = $false}
$app.DisplayAlerts = 0
try {
    $doc = $app.Documents.Open((Join-Path $Workspace '附件1：塔里木大学大学生创新训练项目申报书.doc'),$false,$false)
    $table = $doc.Tables.Item(1)
    function Set-Cell([int]$index,[string]$value) {
        $range = $table.Range.Cells.Item($index).Range
        $range.End = $range.End - 1
        $range.Text = $value
    }
    Set-Cell 2 $payload.title
    Set-Cell 4 '电子信息类 0807（提交前按附件6核对）'
    Set-Cell 6 '2027年3月至2028年2月'
    Set-Cell 13 '待本人填写'; Set-Cell 14 '大二'
    Set-Cell 15 '信息工程学院 通信专业'; Set-Cell 16 '待填写'; Set-Cell 17 '待填写'
    Set-Cell 19 '由负责人据实填写专业学习、实践经历及实际成果。'
    Set-Cell 60 '待指导教师据实填写科研、教学及指导情况。'
    Set-Cell 62 '待教师确认可提供的实验空间、参考仪器、开发及研究指导条件。'
    foreach ($index in @(60,62)) {
        $range=$table.Range.Cells.Item($index).Range
        $range.Rows.Item(1).HeightRule=0
        $range.Rows.Item(1).AllowBreakAcrossPages=$false
    }
    $bodyCells=@()
    for ($i=0;$i -lt 9;$i++) {$bodyCells+=,$table.Range.Cells.Item(63+$i)}
    for ($i=0;$i -lt 9;$i++) {
        $index = 63+$i
        $value = [string]$payload.sections[$i]
        Set-Cell $index $value
        $cell = $table.Range.Cells.Item($index)
        $cell.Range.Font.Name = 'Times New Roman'
        $cell.Range.Font.NameFarEast = '宋体'
        $cell.Range.Font.Size = 10.5
        $cell.Range.ParagraphFormat.LineSpacingRule = 0
        $cell.Range.ParagraphFormat.SpaceAfter = 5
        $cell.Range.ParagraphFormat.SpaceBefore = 0
        $cell.Range.ParagraphFormat.Alignment = 3
        $cell.Range.ParagraphFormat.KeepTogether = -1
        $cell.Range.ParagraphFormat.KeepWithNext = 0
        $cell.Range.Rows.Item(1).HeightRule = 0
        $cell.Range.Rows.Item(1).AllowBreakAcrossPages = $true
        $cell.Range.Paragraphs.Item(1).Range.Font.Bold = $true
        $cell.Range.Paragraphs.Item(1).Range.ParagraphFormat.KeepWithNext = -1
    }
    # Preserve the school template while giving the long scheme a heading ladder.
    for ($i=0;$i -lt 9;$i++) {
        foreach ($paragraph in $table.Range.Cells.Item(63+$i).Range.Paragraphs) {
            $line=$paragraph.Range.Text.Trim()
            if ($line -match '^\d+(\.\d+)?\s' -or $line -match '^表\d+\s') {
                $paragraph.Range.Font.Bold=0
                $heading=$paragraph.Range.Duplicate
                $firstLine=($paragraph.Range.Text -split ([string][char]11),2)[0].TrimEnd([char]13,[char]7)
                $heading.End=$heading.Start+$firstLine.Length
                $heading.Font.Bold=-1
                $paragraph.Range.ParagraphFormat.SpaceBefore=7
                $paragraph.Range.ParagraphFormat.KeepWithNext=-1
            }
        }
    }
    # The original references section follows the system and experiment scheme.
    $table.Range.Cells.Item(66).Range.Paragraphs.Item(1).Range.ParagraphFormat.PageBreakBefore = 0
    # Keep the original three signature rows together on one page.
    # Put its label in the first cell so it cannot be orphaned on the prior page.
    Set-Cell 72 '项目组成员签字：'
    $table.Range.Cells.Item(72).Range.Font.NameFarEast='宋体'
    $table.Range.Cells.Item(72).Range.Font.Size=10.5
    for ($i=72;$i -le 80;$i++) {
        $signature=$table.Range.Cells.Item($i)
        $signature.Range.Rows.AllowBreakAcrossPages=$false
        $signature.Range.ParagraphFormat.KeepWithNext=if ($i -lt 78) {-1} else {0}
    }
    $table.Range.Cells.Item(72).Range.Paragraphs.Item(1).Range.ParagraphFormat.PageBreakBefore=-1
    # Insert each figure at its argument anchor, rather than append them together.
    foreach ($figure in $payload.figures) {
        $range=$doc.Content.Duplicate
        $range.Find.ClearFormatting();$range.Find.Text=[string]$figure.marker;$range.Find.Wrap=0
        if (-not $range.Find.Execute()) {throw ('Missing figure anchor: '+$figure.marker)}
        $range.Text='';$range.Collapse(1)
        $shape = $doc.InlineShapes.AddPicture((Join-Path $Workspace ([string]$figure.path)),$false,$true,$range)
        # WPS may leave Height unchanged when assigning Width despite the lock.
        # Set both dimensions from source pixels; verify saved VML in QA.
        $shape.LockAspectRatio = 0
        $shape.Width = [double]$figure.width_pt
        $shape.Height = [double]$figure.height_pt
        $shape.LockAspectRatio = -1
        $shape.Range.ParagraphFormat.Alignment = 1
        $shape.Range.ParagraphFormat.KeepTogether = -1
        $shape.Range.ParagraphFormat.KeepWithNext = 0
        $shape.AlternativeText = [string]$figure.caption
        $tail=$shape.Range.Duplicate;$tail.Collapse(0)
        $tail.InsertAfter([char]11+[string]$figure.caption)
    }
    foreach ($figure in $payload.figures) {
        $caption = $doc.Content.Duplicate
        $caption.Find.ClearFormatting()
        $caption.Find.Text = [string]$figure.caption
        $caption.Find.Wrap = 0
        if ($caption.Find.Execute()) {
            $caption.ParagraphFormat.KeepWithNext = 0
            $caption.ParagraphFormat.KeepTogether = -1
            $caption.Font.Size=9
        } else { throw 'Expected figure caption missing from native template.' }
    }
    # Numeric/verification records become editable nested Word tables.
    foreach ($record in $payload.tables) {
        $range=$doc.Content.Duplicate
        $range.Find.ClearFormatting();$range.Find.Text=[string]$record.marker;$range.Find.Wrap=0
        if (-not $range.Find.Execute()) {throw ('Missing table anchor: '+$record.marker)}
        $range.Text='';$range.Collapse(1)
        $rowCount=$record.rows.Count;$columnCount=$record.rows[0].Count
        # One non-splittable row keeps the editable record and caption together.
        # It is a pagination container, with no visible panel or borders.
        $holder=$doc.Tables.Add($range,1,1)
        $holder.PreferredWidthType=3;$holder.PreferredWidth=425
        $holder.TopPadding=0;$holder.BottomPadding=0;$holder.LeftPadding=0;$holder.RightPadding=0
        $holder.Rows.HeightRule=0;$holder.Rows.AllowBreakAcrossPages=$false
        foreach ($border in $holder.Borders) {$border.LineStyle=0}
        $holderRange=$holder.Cell(1,1).Range.Duplicate;$holderRange.End=$holderRange.End-1
        $holderRange.Text=[string]$record.caption+"`r"
        $holder.Cell(1,1).Range.Paragraphs.Item(1).Range.Font.Bold=-1
        $holder.Cell(1,1).Range.Paragraphs.Item(1).Range.ParagraphFormat.SpaceAfter=7
        $innerRange=$holder.Cell(1,1).Range.Duplicate;$innerRange.End=$innerRange.End-1;$innerRange.Collapse(0)
        $native=$doc.Tables.Add($innerRange,$rowCount,$columnCount)
        $native.AllowAutoFit=$false
        $native.PreferredWidthType=3;$native.PreferredWidth=425
        $native.Range.Font.NameFarEast='宋体';$native.Range.Font.Name='Times New Roman'
        $native.Range.Font.Size=9.5;$native.Range.Font.Bold=0
        $native.Range.ParagraphFormat.SpaceBefore=0;$native.Range.ParagraphFormat.SpaceAfter=2
        $native.Range.ParagraphFormat.LineSpacingRule=0
        $native.Range.ParagraphFormat.KeepWithNext=-1
        $native.Rows.Item($rowCount).Range.ParagraphFormat.KeepWithNext=0
        $native.TopPadding=3;$native.BottomPadding=3;$native.LeftPadding=5;$native.RightPadding=5
        $native.Rows.AllowBreakAcrossPages=$false
        $native.Rows.Item(1).HeadingFormat=-1
        $widths=@($record.column_widths_pt)
        for ($r=1;$r -le $rowCount;$r++) {
            for ($c=1;$c -le $columnCount;$c++) {
                $targetCell=$native.Cell($r,$c)
                $targetCell.Range.Text=[string]$record.rows[$r-1][$c-1]
                $targetCell.VerticalAlignment=1
                if ($r -eq 1) {$targetCell.Shading.BackgroundPatternColor=15592941;$targetCell.Range.Font.Bold=-1}
                else {$targetCell.Shading.BackgroundPatternColor=16777215}
            }
        }
        for ($c=1;$c -le $columnCount;$c++) {$native.Columns.Item($c).Width=$widths[$c-1]}
        foreach ($edge in @(-1,-2,-3,-4,-5,-6)) {
            $border=$native.Borders.Item($edge)
            $border.LineStyle=1;$border.LineWidth=2;$border.Color=14277081
        }
        $native.Borders.Item(-7).LineStyle=0
        $native.Borders.Item(-8).LineStyle=0
    }
    # An invisible native row for each citation keeps the entire entry together.
    # WPS ignores paragraph KeepTogether inside the continued school-form cell.
    if ($payload.references.Count -gt 0) {
        $anchor=$doc.Content.Duplicate
        $anchor.Find.ClearFormatting();$anchor.Find.Text='[[BIBLIOGRAPHY]]';$anchor.Find.Wrap=0
        if (-not $anchor.Find.Execute()) {throw 'Bibliography anchor missing'}
        $anchor.Text='';$anchor.Collapse(1)
        $bibliography=$doc.Tables.Add($anchor,$payload.references.Count,1)
        $bibliography.AllowAutoFit=$false
        $bibliography.PreferredWidthType=3;$bibliography.PreferredWidth=425
        $bibliography.Columns.Item(1).Width=425
        $bibliography.TopPadding=0;$bibliography.BottomPadding=0
        $bibliography.LeftPadding=0;$bibliography.RightPadding=0
        $bibliography.Rows.AllowBreakAcrossPages=$false
        foreach ($border in $bibliography.Borders) {$border.LineStyle=0}
        for ($i=0;$i -lt $payload.references.Count;$i++) {
            $entry=$bibliography.Cell($i+1,1)
            $entry.Range.Text=[string]$payload.references[$i]
            $entry.Range.Font.Name='Times New Roman';$entry.Range.Font.NameFarEast='宋体'
            $entry.Range.Font.Size=10.5;$entry.Range.Font.Bold=0
            $entry.Range.ParagraphFormat.SpaceBefore=0;$entry.Range.ParagraphFormat.SpaceAfter=5
            $entry.Range.ParagraphFormat.LineSpacingRule=0
            $entry.Range.ParagraphFormat.KeepTogether=-1;$entry.Range.ParagraphFormat.KeepWithNext=0
            $entry.Range.ParagraphFormat.PageBreakBefore=0
        }
    }
    # Cover fields retain the school's logo and original page design.
    foreach ($p in $doc.Paragraphs) {
        $value = $p.Range.Text.Trim()
        if ($value -match '^项目名称：\s*$') {
            $p.Range.Text = '项目名称：'+$payload.title+"`r"
            $p.Range.Font.Size = 10.5
            $p.Range.ParagraphFormat.LeftIndent=0
            $p.Range.ParagraphFormat.RightIndent=0
            $p.Range.ParagraphFormat.Alignment=1
        }
        elseif ($value -match '^所属学院：\s*$') {$p.Range.Text = "所属学院：信息工程学院`r"}
        elseif ($value -match '^起止时间：\s*$') {$p.Range.Text = "起止时间：2027年3月至2028年2月`r"}
        elseif ($value -match '^填\s*写\s*须\s*知$') {$p.Range.ParagraphFormat.PageBreakBefore=-1}
    }
    $doc.Repaginate()
    # WPS may split even a paragraph containing a soft heading line. Compare
    # the native pages of that heading and its first body character explicitly.
    for ($i=0;$i -lt 9;$i++) {
        foreach ($paragraph in $table.Range.Cells.Item(63+$i).Range.Paragraphs) {
            $value=$paragraph.Range.Text
            $split=$value.IndexOf([char]11)
            if ($split -gt 0 -and $value -match '^\d+(\.\d+)?\s') {
                $head=$paragraph.Range.Duplicate;$head.Collapse(1)
                $body=$paragraph.Range.Duplicate;$body.Start=$body.Start+$split+1;$body.Collapse(1)
                if ($head.Information(3) -ne $body.Information(3)) {
                    $paragraph.Range.ParagraphFormat.PageBreakBefore=-1
                    $doc.Repaginate()
                }
            }
        }
    }
    # Ensure a main section label has at least its first body line on its page.
    for ($i=0;$i -lt 9;$i++) {
        $sectionCell=$table.Range.Cells.Item(63+$i)
        if ($sectionCell.Range.Paragraphs.Count -gt 1) {
            $heading=$sectionCell.Range.Paragraphs.Item(1).Range.Duplicate
            $body=$sectionCell.Range.Paragraphs.Item(2).Range.Duplicate
            $heading.Collapse(1);$body.Collapse(1)
            if ($heading.Information(3) -ne $body.Information(3)) {
                $sectionCell.Range.Paragraphs.Item(1).Range.ParagraphFormat.PageBreakBefore=-1
                $doc.Repaginate()
            }
        }
    }
    # Native non-splittable rows protect the three reviewed text blocks. WPS
    # ignores paragraph keep/page-break flags within the continued school row.
    $protectedParagraphs=@()
    foreach ($paragraph in $doc.Paragraphs) {
        $value=$paragraph.Range.Text
        if (($value -match '^\d+(\.\d+)?\s' -and $value.Contains([char]11)) -or $value -match '^(有效早期要求|已形成17篇|图9展示|对288个静态有界误差组合|已核对17个候选引脚)') {
            $protectedParagraphs+=@{start=$paragraph.Range.Start;end=$paragraph.Range.End}
        }
    }
    foreach ($position in ($protectedParagraphs | Sort-Object start -Descending)) {
        $block=$doc.Range($position.start,$position.end)
        $value=$block.Text.TrimEnd([char]13,[char]7)
        $block.End=$block.End-1;$block.Text='';$block.Collapse(1)
        $holder=$doc.Tables.Add($block,1,1)
        $holder.AllowAutoFit=$false;$holder.PreferredWidthType=3;$holder.PreferredWidth=455
        $holder.Columns.Item(1).Width=455
        $holder.TopPadding=0;$holder.BottomPadding=0;$holder.LeftPadding=0;$holder.RightPadding=0
        $holder.Rows.AllowBreakAcrossPages=$false
        foreach ($border in $holder.Borders) {$border.LineStyle=0}
        $target=$holder.Cell(1,1).Range
        $target.Text=$value;$target.Font.Name='Times New Roman';$target.Font.NameFarEast='宋体'
        $target.Font.Size=10.5;$target.Font.Bold=0
        $target.ParagraphFormat.Alignment=3;$target.ParagraphFormat.SpaceAfter=5
        $target.ParagraphFormat.SpaceBefore=0;$target.ParagraphFormat.PageBreakBefore=0
        $target.ParagraphFormat.KeepWithNext=0;$target.ParagraphFormat.LineSpacingRule=0
        $split=$value.IndexOf([char]11)
        if ($split -gt 0) {
            $offset=0
            foreach ($line in ($value -split ([string][char]11))) {
                if ($line -match '^\d+(\.\d+)?\s') {$head=$target.Duplicate;$head.Start=$target.Start+$offset;$head.End=$head.Start+$line.Length;$head.Font.Bold=-1}
                $offset+=$line.Length+1
            }
        }
    }
    foreach ($prefix in @('学院意见：','学校意见：')) {
        $anchor=$doc.Content.Duplicate
        $anchor.Find.ClearFormatting();$anchor.Find.Text=$prefix;$anchor.Find.Wrap=0
        if (-not $anchor.Find.Execute()) {throw 'School approval label missing'}
        $cell=$anchor.Cells.Item(1)
        $cell.Range.Rows.AllowBreakAcrossPages=$false
        if ($prefix -eq '学院意见：') {
            $cell.Range.ParagraphFormat.KeepWithNext=-1
            $cell.Range.Paragraphs.Item(1).Range.ParagraphFormat.PageBreakBefore=-1
        }
    }
    # Nested pagination rows leave empty delimiter paragraphs. Keep their
    # required OOXML presence, while preventing extra full-size blank lines.
    foreach ($bodyCell in $bodyCells) {
        foreach ($paragraph in $bodyCell.Range.Paragraphs) {
            $value=$paragraph.Range.Text.Trim([char]13,[char]7,[char]11,[char]32)
            if ($value.Length -eq 0 -and $paragraph.Range.InlineShapes.Count -eq 0) {
                $paragraph.Range.Font.Size=1
                $paragraph.Range.ParagraphFormat.SpaceBefore=0
                $paragraph.Range.ParagraphFormat.SpaceAfter=0
                $paragraph.Range.ParagraphFormat.LineSpacingRule=4
                $paragraph.Range.ParagraphFormat.LineSpacing=1
                try {$paragraph.Range.ParagraphFormat.LineUnitBefore=0;$paragraph.Range.ParagraphFormat.LineUnitAfter=0} catch {}
            }
        }
    }
    $doc.Repaginate()
    # Keep the school-level innovation label with its first protected body row.
    # WPS ignores KeepWithNext between the outer paragraph and nested table.
    $label=$doc.Content.Duplicate
    $label.Find.ClearFormatting();$label.Find.Text='五、项目的特色与创新点';$label.Find.Wrap=0
    $first=$doc.Content.Duplicate
    $first.Find.ClearFormatting();$first.Find.Text='1 面向支管巡检的完整证据链';$first.Find.Wrap=0
    if (-not $label.Find.Execute() -or -not $first.Find.Execute()) {throw 'Innovation section anchors missing'}
    if ($label.Information(3) -ne $first.Information(3)) {
        $labelText=$label.Text
        $label.Text=''
        $label.ParagraphFormat.SpaceBefore=0;$label.ParagraphFormat.SpaceAfter=0
        $label.ParagraphFormat.LineSpacingRule=4;$label.ParagraphFormat.LineSpacing=1
        $label.Font.Size=1
        $first.Collapse(1)
        $first.InsertBefore($labelText+"`r")
        $restored=$doc.Content.Duplicate
        $restored.Find.ClearFormatting();$restored.Find.Text=$labelText;$restored.Find.Wrap=0
        if (-not $restored.Find.Execute()) {throw 'Innovation label recovery failed'}
        $restored.Font.Bold=-1;$restored.Font.Size=10.5
        $restored.ParagraphFormat.SpaceBefore=0;$restored.ParagraphFormat.SpaceAfter=7
        $doc.Repaginate()
    }
    $candidateDirectory=Join-Path $Workspace $OutputDirectory
    New-Item -ItemType Directory -Path $candidateDirectory -Force | Out-Null
    $target = Join-Path $candidateDirectory '大创申报书_模板填写稿.docx'
    $doc.SaveAs2($target,16)
    $doc.ExportAsFixedFormat((Join-Path $candidateDirectory '大创申报书_模板审阅版.pdf'),17)
    $imagePages=@()
    foreach ($figure in $payload.figures) {
        $caption=$doc.Content.Duplicate
        $caption.Find.ClearFormatting();$caption.Find.Text=[string]$figure.caption;$caption.Find.Wrap=0
        if (-not $caption.Find.Execute()) {throw 'Native caption audit failed'}
        $paragraph=$caption.Paragraphs.Item(1).Range
        $start=$paragraph.Duplicate;$start.Collapse(1)
        $end=$caption.Duplicate;$end.Collapse(0)
        $imagePages+=@{caption=[string]$figure.caption;start_page=$start.Information(3);end_page=$end.Information(3);width_pt=[double]$figure.width_pt}
    }
    $tablePages=@()
    foreach ($record in $payload.tables) {
        $caption=$doc.Content.Duplicate
        $caption.Find.ClearFormatting();$caption.Find.Text=[string]$record.caption;$caption.Find.Wrap=0
        if (-not $caption.Find.Execute()) {throw 'Native table audit failed'}
        $tablePages+=@{caption=[string]$record.caption;page=$caption.Information(3);columns=$record.rows[0].Count;rows=$record.rows.Count}
    }
    @{pages=$doc.ComputeStatistics(2);figures=$imagePages;tables=$tablePages;source='WPS native ranges';physical_validation=$false} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $candidateDirectory 'native_layout.json') -Encoding utf8NoBOM
    Write-Output ('Native template edited; pages='+$doc.ComputeStatistics(2))
    $doc.Close(0)
} finally {
    if ($null -ne $doc) {try {$doc.Close(0)} catch {}}
    if ($priorDocumentCount -eq 0) {try {$app.Quit()} catch {Write-Output 'Native automation session closed'}}
    else {$app.Visible=$priorVisible;$app.DisplayAlerts=$priorAlerts}
}
