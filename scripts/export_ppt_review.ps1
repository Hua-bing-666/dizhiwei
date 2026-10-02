param([Parameter(Mandatory=$true)][string]$InputPptx,
      [Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $InputPptx).Path
$target = [IO.Path]::GetFullPath($OutputPdf)
$app = New-Object -ComObject PowerPoint.Application
try {
    $deck = $app.Presentations.Open($source,$true,$false,$false)
    $deck.SaveAs($target,32)
    Write-Output ('Native PPTX exported; slides='+$deck.Slides.Count)
    $deck.Close()
} finally { $app.Quit() }
