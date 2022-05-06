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
    const voltage1 = values.volt1;
    const voltage2 = values.volt2;

    updateValuesOnScreen(lamda1, lamda2, afr1, afr2);

    applyWarningColors($("#lamda1"), lamda1);
    applyWarningColors($("#lamda2"), lamda2);

    checkErrors($('#bank1Label'), $('#lamda1'), $('#afr1'), voltage1);
    checkErrors($('#bank2Label'), $('#lamda2'), $('#afr2'), voltage2);

    if (lamda1 >= MAX_ABOVE_RED || lamda1 <= MAX_BELOW_RED) {
        applyRedBlinking($("#lamda1"));
    }
    if (lamda2 >= MAX_ABOVE_RED || lamda2 <= MAX_BELOW_RED) {
        applyRedBlinking($("#lamda2"));
    }
});


function updateValuesOnScreen(lamda1, lamda2, afr1, afr2) {
    const decimalPlaces = $("input[name='nachkommastellen']:checked").val();

    $('#lamda1').html(lamda1.toFixed(decimalPlaces) + " &lambda;");
    $('#lamda2').html(lamda2.toFixed(decimalPlaces) + " &lambda;");
    $('#afr1').html(afr1.toFixed(2) + " AFR");
    $('#afr2').html(afr2.toFixed(2) + " AFR");
}

function checkErrors(htmlBankLabel, htmlLamda, htmlAFR, voltage) {
    label = htmlBankLabel.html();
    color = "#000000";
    lamda = htmlLamda.html();
    afr = htmlAFR.html();

    if (Math.abs(voltage) <= 0.15) {
        // label += " - Fehler";
        color= "#b30000";
        lamda = "Fehler";
        afr = "--------";
    } else if (Math.abs(voltage) <= 0.2) {
        // label += " - Heizphase";
        color= "#b30000";
        lamda = "Heizphase";
        afr = "--------";
    }

    htmlBankLabel.html(label);
    htmlBankLabel.css("color", color);
    htmlLamda.html(lamda);
    htmlAFR.html(afr);
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
    htmlElement.css("color", "rgba(0,0,0,0)");
}

function Sleep(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}