# Descarga el histórico oficial y exporta su tabla Access para la auditoría CPV.
# Requiere Microsoft Access Driver (*.mdb, *.accdb) de 64 bits.
$ErrorActionPreference = 'Stop'
$raiz = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$datos = Join-Path $raiz 'data/electoral'
$access = Join-Path $datos 'historico_secciones_ine_2025.accdb'
$csv = Join-Path $datos 'historico_secciones_ine_2025.csv'
$url = 'https://cartografia.ine.mx/mapoteca/historicos/HISTORICO_SECC_ELECT_PEF_1994-PEF2024_Corte_diciembre2025.accdb'
if (-not (Test-Path -LiteralPath $access)) {
    Invoke-WebRequest -Uri $url -OutFile $access
}
$conexion = [System.Data.Odbc.OdbcConnection]::new(
    "Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=$access;"
)
try {
    $conexion.Open()
    $comando = $conexion.CreateCommand()
    $comando.CommandText = 'SELECT * FROM [HISTORICO_SECC_ELECT_PEF1994-PEF2024_CORTE_diciembre2025]'
    $adaptador = [System.Data.Odbc.OdbcDataAdapter]::new($comando)
    $tabla = [System.Data.DataTable]::new()
    [void]$adaptador.Fill($tabla)
    $tabla | Export-Csv -LiteralPath $csv -NoTypeInformation -Encoding utf8
    Write-Output "Exportadas $($tabla.Rows.Count) filas a $csv"
} finally {
    $conexion.Dispose()
}
