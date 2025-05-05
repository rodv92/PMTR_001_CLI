<?php
    //open connection to mysql db
    $connection = mysqli_connect("localhost","pmtr_user","password","PMTR") or die("Error " . mysqli_error($connection));
    //fetch table rows from mysql db
    $sql = "select epoch,
    L1_voltage_V,L2_voltage_V,L3_voltage_V,
    L1_current_A,L2_current_A,L3_current_A,
    L1_active_power_W,L2_active_power_W,L3_active_power_W,
    L1_energy_kWh,L2_energy_kWh,L3_energy_kWh,
    L1_frequency_Hz,L2_frequency_Hz,L3_frequency_Hz,
    L1_pf,L2_pf,L3_pf
    from instant WHERE epoch >= now() - INTERVAL 1 DAY";
    $result = mysqli_query($connection, $sql) or die("Error in Selecting " . mysqli_error($connection));

     $temparray = array();
    while($row =mysqli_fetch_assoc($result))
    {
        $temparray[] = $row;
    }
    echo json_encode($temparray);
?>
