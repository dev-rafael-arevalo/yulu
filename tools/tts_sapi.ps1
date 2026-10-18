# Sintetiza una lista de frases a WAV con la voz SAPI5 de Windows indicada.
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File tools/tts_sapi.ps1 -JobFile <ruta.json> -Voice "Microsoft Sabina Desktop"
# El JSON es una lista de objetos {"file": "<ruta de salida>", "text": "<frase>", "ssml": "<documento SSML opcional>"}.
# Si "ssml" está presente se usa SpeakSsml (prosodia: ritmo, tono, volumen y pausas); si no, Speak.
param(
    [Parameter(Mandatory = $true)][string]$JobFile,
    [string]$Voice = "Microsoft Sabina Desktop",
    [int]$Rate = -1
)
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $synth.SelectVoice($Voice)
} catch {
    Write-Output "AVISO: voz '$Voice' no disponible; se usa la voz predeterminada."
}
$synth.Rate = $Rate
$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(22050, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
$jobs = Get-Content -Raw -Encoding UTF8 $JobFile | ConvertFrom-Json
$count = 0
foreach ($job in $jobs) {
    $synth.SetOutputToWaveFile($job.file, $format)
    try {
        if ($job.ssml) {
            $synth.SpeakSsml($job.ssml)
        } else {
            $synth.Speak($job.text)
        }
    } catch {
        Write-Output "AVISO: fallo SSML en $($job.file); se usa texto plano. $($_.Exception.Message)"
        $synth.Speak($job.text)
    }
    $synth.SetOutputToNull()
    $count++
}
$synth.Dispose()
Write-Output "Generados $count archivos con la voz: $($synth.Voice.Name)"
