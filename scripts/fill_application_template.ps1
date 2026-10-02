param([string]$Workspace = 'C:\Users\Lenovo\Desktop\大创想法')
$ErrorActionPreference = 'Stop'
$payload = Get-Content -LiteralPath (Join-Path $Workspace 'tmp\reference_review\application_payload.json') -Raw | ConvertFrom-Json
$app = New-Object -ComObject kwps.Application
$app.Visible = $false
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
    Set-Cell 19 '尚未提供，由本人据实填写，不能照抄案例经历。'
    Set-Cell 60 '待指导教师据实填写科研、教学及指导情况。'
    Set-Cell 62 '待教师确认可提供的实验空间、参考仪器、开发及研究指导条件。'
    foreach ($index in @(60,62)) {
        $range=$table.Range.Cells.Item($index).Range
        $range.Rows.Item(1).HeightRule=0
        $range.Rows.Item(1).AllowBreakAcrossPages=$false
    }
    for ($i=0;$i -lt 9;$i++) {
        $index = 63+$i
        $value = [string]$payload.sections[$i]
        if ($i -eq 8) {$value += "`r`r项目组成员签字："}
        Set-Cell $index $value
        $cell = $table.Range.Cells.Item($index)
        $cell.Range.Font.Name = 'Times New Roman'
        $cell.Range.Font.NameFarEast = '宋体'
        $cell.Range.Font.Size = 10.5
        $cell.Range.ParagraphFormat.LineSpacingRule = 0
        $cell.Range.ParagraphFormat.SpaceAfter = 5
        $cell.Range.ParagraphFormat.SpaceBefore = 0
        $cell.Range.ParagraphFormat.Alignment = 0
        $cell.Range.ParagraphFormat.KeepTogether = 0
        $cell.Range.ParagraphFormat.KeepWithNext = 0
        $cell.Range.Rows.Item(1).HeightRule = 0
        $cell.Range.Rows.Item(1).AllowBreakAcrossPages = $true
        $cell.Range.Paragraphs.Item(1).Range.Font.Bold = $true
        $cell.Range.Paragraphs.Item(1).Range.ParagraphFormat.KeepWithNext = -1
    }
    # Start the research-basis section on a fresh page after the design figures.
    $table.Range.Cells.Item(66).Range.Paragraphs.Item(1).Range.ParagraphFormat.PageBreakBefore = -1
    # Add native inline drawings to the end of the project scheme section.
    $cell = $table.Range.Cells.Item(65)
    foreach ($figure in $payload.figures) {
        $range = $cell.Range.Duplicate
        $range.End = $range.End - 1
        $range.Collapse(0)
        $range.InsertBefore("`r"+[string]$figure.caption+"`r")
        $range = $cell.Range.Duplicate; $range.End = $range.End - 1; $range.Collapse(0)
        $shape = $doc.InlineShapes.AddPicture((Join-Path $Workspace ([string]$figure.path)),$false,$true,$range)
        $shape.LockAspectRatio = -1; $shape.Width = 435
        $shape.Range.ParagraphFormat.Alignment = 1
        $shape.Range.ParagraphFormat.KeepWithNext = 0
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
    $target = Join-Path $Workspace 'deliverables\大创申报书_模板填写稿.docx'
    $doc.SaveAs2($target,16)
    $doc.ExportAsFixedFormat((Join-Path $Workspace 'deliverables\大创申报书_模板审阅版.pdf'),17)
    Write-Output ('Native template edited; pages='+$doc.ComputeStatistics(2))
    $doc.Close(0)
} finally {try {$app.Quit()} catch {Write-Output 'Native automation session closed'}}
