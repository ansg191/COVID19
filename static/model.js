let store = {};
store.today = Math.floor((new Date() - new Date(2019, 11, 31)) / 86400000);
store.country = $('#start-country').data('country');
store.options = {
    countries: [],
    min_date: {}
};

$('document').ready(function () {
    getData(store.country);
    store.picker = new Pikaday({
        field: document.getElementById('datepicker'),
        minDate: new Date(2020, 0, 1),
        maxDate: new Date(),
        defaultDate: new Date(),
        setDefaultDate: true,
        onSelect: function (e) {
            store.today = Math.round((e - new Date(2019, 11, 31)) / 86400000);
            console.log("Changing date to ", store.today);
            updateOptions(store.today);
            getData(store.country);
        }
    });
    $('#country').dropdown({
        onChange: function (value, text, $selectedItem) {
            countryChange(value);
        }
    });
    $('.ui.search.selection.dropdown').css({'width': '75%', 'text-align': 'center', 'height': '50px'});
    updateOptions(store.today);
});

let updateOptions = function (date) {
    $.when(
        $.ajax({
            url: "/_get_country_options",
            dataType: 'json',
            data: {date: date},
            success: function (e) {
                store.options = e;
            }
        })
    ).then(function () {
        // $('#country').find('option').remove();
        // let select = document.getElementById('suggestions');
        // for (let i = 0; i < store.options.countries.length; i++) {
        //     let opt = document.createElement('option');
        //     opt.value = store.options.countries[i];
        //     opt.innerHTML = store.options.countries[i];
        //     select.appendChild(opt);
        // }
        let values = [];
        for (let i = 0; i < store.options.countries.length; i++) {
            // console.log(store.options.countries);
            let country = store.options.countries[i];
            values.push({value: country, text: country, name: country});
        }
        // console.log(values);
        let dropdown = $('#country');
        dropdown.dropdown('change values', values);
        dropdown.dropdown('set selected', store.country);
        $(".ui.search.selection.dropdown div:eq(1) .item").css('font-size', '15px');
        $(".ui.search.selection.dropdown input").css({'top': '-20px', 'text-align': 'center', 'font-size': '35px'});
        let parts = store.options.min_date[store.country].split('-');
        store.picker.setMinDate(new Date(parts[0], parts[1] - 1, parts[2]));
    })
};

let countryChange = function (country) {
    if (store.options.countries.includes(country)) {
        console.log("Switching to ", country);
        $("#country").blur();
        store.country = country;
        $('.ui.search.selection.dropdown .text').css({'font-size': '35px', 'top': '4px'});
        let parts = store.options.min_date[store.country].split('-');
        store.picker.setMinDate(new Date(parts[0], parts[1] - 1, parts[2]));
        getData(country);
    }
};

let getData = function (country) {
    // $.ajax({
    //     url: "_get_country_cases",
    //     dataType: 'json',
    //     data: {country: country},
    //     success: function (data) {
    //         $.ajax({
    //             url: "_get_lmfit_cases",
    //             dataType: 'json',
    //             data: {country: country},
    //             success: function (fit) {
    //                 draw(data, fit);
    //             }
    //         });
    //     }
    // });
    $.when(
        $.ajax({
            url: "/_get_country_cases",
            dataType: 'json',
            data: {country: country, date: store.today},
            success: function (data) {
                store.data = data;
            }
        }),
        $.ajax({
            url: "/_get_lmfit_cases",
            dataType: 'json',
            data: {country: country, date: store.today},
            success: function (fit) {
                store.fit = fit;
            }
        })
    ).then(function () {
        draw(store.data, store.fit);
        getDeathData(country);
    });
};

Date.prototype.addDays = function(days) {
    let date = new Date(this.valueOf());
    date.setDate(date.getDate() + days);
    return date;
};

let diff = function (x) {
    let arr = [0];
    for (let i = 1; i < x.length; i++) {
        arr.push(x[i] - x[i - 1])
    }
    return arr;
};

let rollmean = function (x) {
    let arr = [Number.NaN, Number.NaN];
    for (let i = 1; i < x.length - 1; i++) {
        let mean = (x[i - 1] + x[i] + x[i + 1]) / 3.0;
        arr.push(mean);
    }
    return arr;
};

let shift = function (x) {
    let arr = [Number.NaN];
    for (let i = 0; i < x.length - 1; i++) {
        arr.push(x[i])
    }
    return arr;
};

let updateCaseText = function (y, x0, y0, currentDay) {
    $('#current-cases-txt').find('h3').text(y[y.length - 1].toLocaleString());
    $('#pred-cases-txt').find('h3').text(y0[y0.length - 1].toLocaleString());
    $('#tom-new-cases-txt').find('h3').text((y0[currentDay + 1] - y0[currentDay]).toLocaleString());
    $('#double-rate-txt h3').text((y.length - y.findIndex(n => n > y[y.length - 1] / 2)).toLocaleString() + " days");
    $('#compl-date-txt h3').text((new Date(2019, 11, 31)).addDays(x0[x0.length - 1]).toDateString())
    $('#new-cases-txt h3').text((y[y.length - 1] - y[y.length - 2]).toLocaleString());
};

let draw = function (data, fit) {
    let x = Object.keys(data).map(function (item) {
        return parseInt(item)
    });
    let y = Object.values(data);
    let x0 = Object.keys(fit).map(function (item) {
        return parseInt(item)
    });
    let y0 = Object.values(fit);
    let currentDay = x[x.length - 1];
    updateCaseText(y, x0, y0, x0.indexOf(currentDay));
    currentCases(x, y, x0, y0, currentDay);
    predCases(x, y, x0, y0);
    logCases(x, y, x0, y0);
    newVsTotal(y, y0);
    newCases(x, y);
    newPredCases(x, y, x0, y0, currentDay);
    growthRate(x, y);
};

let currentCases = function (x, y, x0, y0, currentDay) {
    let trace1 = {
        x: x,
        y: y,
        mode: 'markers',
        type: 'scatter',
        name: 'Data'
    };
    let index = x0.indexOf(currentDay);
    let trace2 = {
        x: x0.slice(0, index + 1),
        y: y0.slice(0, index + 1),
        mode: 'lines',
        type: 'scatter',
        name: 'Fit'
    };
    let layout = {
        title: {text: 'Total Cases', y: 0.9, x: 0.5, xanchor: 'center', yanchor: 'bottom'},
        xaxis: {title: 'Day'},
        yaxis: {title: 'Total Cases'},
        font: {family: "Courier New, monospace", size: 18},
        legend: {x: 0.01, y: 0.99, bgcolor: 'rgba(0,0,0,0}'},
        // plot_bgcolor: "rgba(56,252,255,0.24)"
    };
    let config = {responsive: true};
    Plotly.newPlot('current-cases', [trace1, trace2], layout, config);
};

let predCases = function (x, y, x0, y0) {
    let trace1 = {
        x: x,
        y: y,
        mode: 'markers',
        type: 'scatter',
        name: 'Data'
    };
    let trace2 = {
        x: x0,
        y: y0,
        mode: 'lines',
        type: 'scatter',
        name: 'Prediction'
    };
    let layout = {
        title: {text: 'Total Predicted Cases', y: 0.9, x: 0.5, xanchor: 'center', yanchor: 'bottom'},
        xaxis: {title: 'Day'},
        // yaxis: {title: 'Total Cases'},
        font: {family: "Courier New, monospace", size: 18},
        legend: {x: 0.01, y: 0.99, bgcolor: 'rgba(0,0,0,0}'}
    };
    let config = {responsive: true};
    Plotly.newPlot('pred-cases', [trace1, trace2], layout, config);
};

let logCases = function (x, y, x0, y0) {
    let index = y.findIndex(n => n > 100);
    x = x.slice(index);
    y = y.slice(index);
    let doubleRate = y.length - y.findIndex(n => n > y[y.length - 1] / 2);
    let trace1 = {
        x: x,
        y: y,
        mode: 'markers',
        type: 'scatter',
        name: 'Data'
    };
    let trace2 = {
        x: x0.slice(index),
        y: y0.slice(index),
        mode: 'lines',
        type: 'scatter',
        name: 'Prediction'
    };
    let trace3 = {
        x: x.map(n => n + y.length - 1),
        y: x.map(n => y[y.length - 1] * Math.pow(2, (n - x[0]) / doubleRate)),
        mode: 'lines',
        type: 'scatter',
        line: {dash: 'dash'},
        opacity: 0.5,
        showlegend: false,
        text: "Double Every " + doubleRate + " Days"
    };
    let layout = {
        title: {text: 'Total Predicted Cases on Log Scale', y: 0.9, x: 0.5, xanchor: 'center', yanchor: 'bottom'},
        xaxis: {title: 'Day'},
        yaxis: {title: 'Total Cases', type: 'log'},
        font: {family: "Courier New, monospace", size: 18},
        legend: {x: 0.01, y: 0.99, bgcolor: 'rgba(0,0,0,0}'},
        annotations: [{
            x: 0.01,
            y: 1.1,
            xref: 'paper',
            yref: 'paper',
            text: "Doubled in " + doubleRate + " days",
            showarrow: false
        }]
    };
    let config = {responsive: true};
    Plotly.newPlot('log-cases', [trace1, trace2, trace3], layout, config);
};

let newVsTotal = function (x, x0) {
    let y = rollmean(diff(x));
    let y0 = rollmean(diff(x0));
    let trace1 = {
        x: x,
        y: y,
        mode: 'lines+markers',
        type: 'scatter',
        name: 'Data'
    };
    let trace2 = {
        x: x0,
        y: y0,
        mode: 'lines',
        type: 'scatter',
        name: 'Prediction'
    };
    let layout = {
        title: {
            text: 'New Cases vs Total Cases<br>3 Day Rolling Mean',
            y: 0.9,
            x: 0.5,
            xanchor: 'center',
            yanchor: 'bottom'
        },
        xaxis: {
            title: 'Total Cases',
            type: 'log',
            range: [1, Math.ceil(Math.log10(Math.max(Math.max(...x), Math.max(...x0))))]
        },
        yaxis: {
            title: 'New Cases',
            type: 'log',
            range: [0, Math.ceil(Math.log10(Math.max(Math.max(...y), Math.max(...y0))))]
        },
        font: {family: "Courier New, monospace", size: 18},
        legend: {x: 0.01, y: 0.99, bgcolor: 'rgba(0,0,0,0}'}
    };
    let config = {responsive: true};
    Plotly.newPlot('new-vs-total', [trace1, trace2], layout, config);
};

let newCases = function (x, y) {
    let index = y.findIndex(n => n > 100);
    let ydiff = diff(y);
    let trace1 = {
        x: x.slice(index),
        y: ydiff.slice(index),
        type: 'bar',
        text: ydiff.slice(index).map(String),
        textposition: 'auto'
    };

    let layout = {
        title: {text: 'New Cases Per Day', y: 0.9, x: 0.5, xanchor: 'center', yanchor: 'bottom'},
        xaxis: {title: 'Day'},
        yaxis: {title: 'New Cases'},
        font: {family: "Courier New, monospace", size: 18},
        legend: {x: 0.01, y: 0.99, bgcolor: 'rgba(0,0,0,0}'}
    };
    let config = {responsive: true};
    Plotly.newPlot('new-cases', [trace1], layout, config);
};

let newPredCases = function (x, y, x0, y0, currentDay) {
    let index = y.findIndex(n => n > 100);
    let yDiff = diff(y);
    let y0Diff = diff(y0);
    let trace1 = {
        x: x.slice(index),
        y: yDiff.slice(index),
        type: 'bar',
        text: yDiff.slice(index).map(String),
        textposition: 'auto',
        name: 'Data'
    };

    let index2 = x0.indexOf(currentDay);
    let index3 = y0Diff.slice(index2).findIndex(n => n < 100);
    let trace2 = {
        x: x0.slice(index2 + 1, index3 + index2),
        y: y0Diff.slice(index2 + 1, index3 + index2),
        type: 'bar',
        text: y0Diff.slice(index2 + 1).map(String),
        textposition: 'auto',
        name: 'Prediction'
    };

    let layout = {
        title: {
            text: "New Cases Per Day To Reach " + y0[y0.length - 1].toLocaleString() + " Cases",
            y: 0.9,
            x: 0.5,
            xanchor: 'center',
            yanchor: 'bottom'
        },
        xaxis: {title: 'Day'},
        yaxis: {title: 'New Cases'},
        font: {family: "Courier New, monospace", size: 18},
        legend: {x: 0.01, y: 0.99, bgcolor: 'rgba(0,0,0,0}'}
    };
    let config = {responsive: true};
    Plotly.newPlot('new-pred-cases', [trace1, trace2], layout, config);
};

let growthRate = function (x, y) {
    let index = y.findIndex(n => n > 100);
    let y0 = diff(y);
    let yNew = shift(y0);
    let result = rollmean(y0.map(function (n, i) {
        return n / yNew[i];
    }));
    let trace1 = {
        x: x.slice(index),
        y: result.slice(index),
        mode: 'lines+markers',
        type: 'scatter'
    };
    let trace2 = {
        x: [x[index], x[x.length - 1]],
        y: [1, 1],
        mode: 'lines',
        type: 'scatter'
    };
    let layout = {
        title: {text: "Growth Rate<br>3 Day Rolling Mean", y: 0.9, x: 0.5, xanchor: 'center', yanchor: 'bottom'},
        xaxis: {title: 'Day', range: [x[index], x[x.length - 1]]},
        yaxis: {title: 'Growth Rate', range: [0, 2]},
        font: {family: "Courier New, monospace", size: 18},
        showlegend: false
    };
    let config = {responsive: true};
    Plotly.newPlot('growth-rate', [trace1, trace2], layout, config);
};