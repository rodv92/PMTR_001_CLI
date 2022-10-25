<?php
    //open connection to mysql db
    $connection = mysqli_connect("localhost","pmtr_user","password","PMTR") or die("Error " . mysqli_error($connection));
    //fetch table rows from mysql db
    $sql = "select epoch,L1_voltage_V,L1_current_A,L1_active_power_W,L1_energy_kWh,L1_frequency_Hz,L1_pf from instant";
    $result = mysqli_query($connection, $sql) or die("Error in Selecting " . mysqli_error($connection));

     $temparray = array();
    while($row =mysqli_fetch_assoc($result))
    {
        $temparray[] = $row;
    }
    echo json_encode($temparray);
?>
