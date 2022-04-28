var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function () {
    let browserTime = new Date().toISOString();

    socket.emit('connected', {
        data: browserTime
    });

})

socket.on('disconnect', function () {
    socket.emit('disconnect', {
        data: 'User Disconnected'
    });

})

socket.on('newValues', function (values) {
    // console.log(JSON.stringify(values));

    let decimalPlaces = $("input[name='gender']:checked").val();
    values.lamda1 = values.lamda1.toFixed(decimalPlaces);
    values.lamda2 = values.lamda2.toFixed(decimalPlaces);

    // Checken ob bei Bank 1 ein Fehler oder Heizphase vorliegt
    if (0 - Math.abs(values.lamda1) <= 0.15) {
        $('#bank1Label').html("Bank 1 - Fehler");
        $('#bank1Label').css("color", "#b30000");
        $('#lamda1').html("---------");
        $('#afr1').html("--------");

    } else if (0.4 - Math.abs(values.lamda1) <= 0.2) {
        $('#bank1Label').html("Bank 1 - Heizphase");
        $('#bank1Label').css("color", "#b30000");
        $('#lamda1').html("---------");
        $('#afr1').html("--------");

    } else {
        $('#bank1Label').html("Bank 1");
        $('#bank1Label').css("color", "#000000");
        $('#lamda1').html(values.lamda1.toFixed(3) + " &lambda;");
        $('#afr1').html(values.afr1.toFixed(2) + " AFR");
    }

    // Checken ob bei Bank 2 ein Fehler oder Heizphase vorliegt
    if (0 - Math.abs(values.lamda2) <= 0.15) {
        $('#bank2Label').html("Bank 2 - Fehler");
        $('#bank2Label').css("color", "#b30000");
        $('#lamda2').html("---------");
        $('#afr2').html("--------");

    } else if (0.4 - Math.abs(values.lamda2) <= 0.2) {
        $('#bank2Label').html("Bank 2 - Heizphase");
        $('#bank2Label').css("color", "#b30000");
        $('#lamda2').html("---------");
        $('#afr2').html("--------");

    } else {
        $('#bank2Label').html("Bank 2");
        $('#bank2Label').css("color", "#000000");
        $('#lamda2').html(values.lamda2.toFixed(3) + " &lambda;");
        $('#afr2').html(values.afr2.toFixed(2) + " AFR");
    }

    // console.log("Volt 1: " + values.volt1.toFixed(2));
    // console.log("Volt 2: " + values.volt2.toFixed(2));

    // Sind die Werte von Lamda entsprechend, wird der Text erst Orange und dann Rot
    if (values.lamda1 >= 1.12 || values.lamda1 <= 0.86) {
        if (values.lamda1 >= 1.20 || values.lamda1 <= 0.80) {
            $('#lamda1').css("color", "#b30000");
            // $('#afr1').css("color", "#b30000");
        } else {
            $('#lamda1').css("color", "#e36f27");
            // $('#afr1').css("color", "#e36f27");
        }
    } else {
        $('#lamda1').css("color", "#000000");
        // $('#afr1').css("color", "#000000");
    }

    if (values.lamda2 >= 1.12 || values.lamda2 <= 0.86) {
        if (values.lamda2 >= 1.20 || values.lamda2 <= 0.80) {
            $('#lamda2').css("color", "#b30000");
            // $('#afr2').css("color", "#b30000");
        } else {
            $('#lamda2').css("color", "#e36f27");
            // $('#afr2').css("color", "#e36f27");
        }
    } else {
        $('#lamda2').css("color", "#000000");
        // $('#afr2').css("color", "#000000");
    }

})
