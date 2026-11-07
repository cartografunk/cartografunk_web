param(
    [string]$Source = 'C:\cartografunk_web\data\electoral\ccol_ine_2022_nacional.mdb',
    [string]$Destination = 'C:\cartografunk_web\data\electoral\ccol_ine_2022_nacional.csv'
)

# Exporta únicamente la tabla pública CatalogoColonia de un MDB local del INE.
$connection = [System.Data.OleDb.OleDbConnection]::new(
    "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=$Source;Mode=Read;"
)
$connection.Open()
try {
    $command = $connection.CreateCommand()
    $command.CommandText = 'SELECT * FROM CatalogoColonia'
    $adapter = [System.Data.OleDb.OleDbDataAdapter]::new($command)
    $table = [System.Data.DataTable]::new()
    [void]$adapter.Fill($table)
    $table | Export-Csv -LiteralPath $Destination -NoTypeInformation -Encoding utf8
    Write-Output "Filas exportadas: $($table.Rows.Count)"
} finally {
    $connection.Close()
}
