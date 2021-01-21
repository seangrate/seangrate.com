Plotly.d3.csv('https://raw.githubusercontent.com/plotly/datasets/master/clebsch-cubic.csv', function(err, rows){
  function unpack(rows, key) {
  return rows.map(function(row) {return parseFloat(row[key]); });
}

function constrain(xs, ys, zs, vals) {
    let newX = [];
    let newY = [];
    let newZ = [];
    let newVals = [];

    for (let i = 0; i < xs.length; i++) {
        if (Math.sqrt(Math.pow(xs[i], 2) + Math.pow(ys[i], 2) + Math.pow(zs[i], 2)) <= 2) {
            newX.push(xs[i]);
            newY.push(ys[i]);
            newZ.push(zs[i]);
            newVals.push(vals[i]);
        }
    }



    return [newX, newY, newZ, newVals];
}

let data = constrain(unpack(rows, 'x'), unpack(rows, 'y'), unpack(rows, 'z'), unpack(rows, 'value'));
let x = data[0];
let y = data[1];
let z = data[2];
let vals = data[3];

let layout = {
    // width: Math.floor(document.getElementById("clebsh_plot").offsetWidth / 2),
    // height: 900,
    autosize: true,
    margin: {t: 0, b: 0, l: 0, r: 0},
    scene: {camera: {projection: {type: 'orthographic'}}},
}

Plotly.newPlot('clebsh_plot', [{type: 'isosurface',
                                x: x,
                                y: y,
                                z: z,
                                value: vals,
                                isomin: 0,
                                isomax: 0,
                                surface: {show: true, count: 1, fill: 1},
                                showscale: false}],
                layout, {displayModeBar: false});
});