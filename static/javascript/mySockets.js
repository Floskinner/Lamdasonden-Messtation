const socket = io.connect('http://' + document.domain + ':' + location.port);

const RED = "rgb(179, 0, 0)";
const ORANGE = "rgb(227, 111, 39)";
const BLACK = "rgb(0, 0, 0)";

const MAX_ABOVE_ORANGE = 1.12;
const MAX_ABOVE_RED = 1.20;

const MAX_BELOW_ORANGE = 0.86;
const MAX_BELOW_RED = 0.80;

socket.on('connect', function () {
    let browserTime = new Date().toISOString();

    socket.emit('connected', {
        data: browserTime
    });

});

socket.on('disconnect', function () {
    socket.emit('disconnect', {
        data: 'User Disconnected'
    });

});

socket.on('newValues', function (values) {
    // console.log(JSON.stringify(values));

    const lamda1 = values.lamda1;
    const lamda2 = values.lamda2;
    const afr1 = values.afr1;
    const afr2 = values.afr2;

    updateValuesOnScreen(lamda1, lamda2, afr1, afr2);

    applyWarningColors($("#lamda1"), lamda1);
    applyWarningColors($("#lamda2"), lamda2);

    if (lamda1 >= MAX_ABOVE_RED || lamda1 <= MAX_BELOW_RED ){
        applyRedBlinking($("#lamda1"));
    }
    if (lamda2 >= MAX_ABOVE_RED || lamda2 <= MAX_BELOW_RED ){
        applyRedBlinking($("#lamda2"));
    }

    // // Checken ob bei Bank 1 ein Fehler oder Heizphase vorliegt
    // if (0 - Math.abs(values.lamda1) <= 0.15) {
    //     $('#bank1Label').html("Bank 1 - Fehler");
    //     $('#bank1Label').css("color", "#b30000");
    //     $('#lamda1').html("---------");
    //     $('#afr1').html("--------");

    // } else if (0.4 - Math.abs(values.lamda1) <= 0.2) {
    //     $('#bank1Label').html("Bank 1 - Heizphase");
    //     $('#bank1Label').css("color", "#b30000");
    //     $('#lamda1').html("---------");
    //     $('#afr1').html("--------");

    // } else {
    //     $('#bank1Label').html("Bank 1");
    //     $('#bank1Label').css("color", "#000000");
    //     $('#lamda1').html(values.lamda1.toFixed(3) + " &lambda;");
    //     $('#afr1').html(values.afr1.toFixed(2) + " AFR");
    // }

    // // Checken ob bei Bank 2 ein Fehler oder Heizphase vorliegt
    // if (0 - Math.abs(values.lamda2) <= 0.15) {
    //     $('#bank2Label').html("Bank 2 - Fehler");
    //     $('#bank2Label').css("color", "#b30000");
    //     $('#lamda2').html("---------");
    //     $('#afr2').html("--------");

    // } else if (0.4 - Math.abs(values.lamda2) <= 0.2) {
    //     $('#bank2Label').html("Bank 2 - Heizphase");
    //     $('#bank2Label').css("color", "#b30000");
    //     $('#lamda2').html("---------");
    //     $('#afr2').html("--------");

    // } else {
    //     $('#bank2Label').html("Bank 2");
    //     $('#bank2Label').css("color", "#000000");
    //     $('#lamda2').html(values.lamda2.toFixed(3) + " &lambda;");
    //     $('#afr2').html(values.afr2.toFixed(2) + " AFR");
    // }
});


function updateValuesOnScreen(lamda1, lamda2, afr1, afr2) {
    const decimalPlaces = $("input[name='nachkommastellen']:checked").val();

    $('#lamda1').html(lamda1.toFixed(decimalPlaces) + " &lambda;");
    $('#lamda2').html(lamda2.toFixed(decimalPlaces) + " &lambda;");
    $('#afr1').html(afr1.toFixed(2) + " AFR");
    $('#afr2').html(afr2.toFixed(2) + " AFR");
}

function applyWarningColors(htmlElement, lamdaValue) {
    // Sind die Werte von Lamda entsprechend, wird der Text erst Orange und dann Rot
    if (lamdaValue >= MAX_ABOVE_ORANGE || lamdaValue <= MAX_BELOW_ORANGE) {
        if (lamdaValue >= MAX_ABOVE_RED || lamdaValue <= MAX_BELOW_RED) {
            htmlElement.css("color", RED);
        } else {
            htmlElement.css("color", ORANGE);
        }
    } else {
        htmlElement.css("color", BLACK);
    }
}

async function applyRedBlinking(htmlElement) {
    await Sleep(UPDATE_INTERVALL / 2);
    htmlElement.css("color", BLACK);
}

function Sleep(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}