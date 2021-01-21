let pointCount = 100;
let min_t = -1;
let max_t = 1;
let i, t;

let x = [];
let y = [];
let z = [];

for(i = 0; i < pointCount; i++)
{
    t = min_t + i * ((max_t - min_t) / pointCount);
    x.push(t);
    y.push(Math.pow(t, 2));
    z.push(Math.pow(t, 3))
}
              
// https://plotly.com/javascript/reference/#layout-scene-camera
// let updatemenus=[
//     {
//         buttons: [
//             {
//                 args: [{'scene': {'camera': {'up': {'x': 0, 'y': 0, 'z': 1},
//                                              'center': {'x': 0, 'y': 0, 'z': 0},
//                                              'eye': {'x': 1.25, 'y': 1.25, 'z': 1.25},
//                                              'projection': {'type': 'orthographic'}
//                                             }
//                                  }
//                         }],
//                 label: 'Default',
//                 method: 'relayout'
//             },
//             {
//                 args: [{'scene': {'camera': {'up': {'x': 0, 'y': 0, 'z': 1},
//                                             'center': {'x': 0, 'y': 0.5, 'z': 0},
//                                             'eye': {'x': -1, 'y': 0.5, 'z': 0},
//                                              'projection': {'type': 'orthographic'}
//                                             }
//                                  }
//                         }],
//                 label:'Project onto X',
//                 method:'relayout'
//             },
//             {
//                 args: [{'scene': {'camera': {'up': {'x': 0, 'y': 0, 'z': 1},
//                                              'center': {'x': 0, 'y': 0.5, 'z': 0},
//                                              'eye': {'x': 0, 'y': 0, 'z': 0},
//                                              'projection': {'type': 'orthographic'}
//                                             }
//                                  }
//                         }],
//                 label:'Project onto Y',
//                 method:'relayout'
//             },
//             {
//                 args: [{'scene': {'camera': {'up': {'x': 0, 'y': 1, 'z': 0},
//                                              'center': {'x': 0, 'y': 0.5, 'z': 0},
//                                              'eye': {'x': 0, 'y': 0, 'z': 1},
//                                              'projection': {'type': 'orthographic'}
//                                             }
//                                  }
//                         }],
//                 label:'Project onto Z',
//                 method:'relayout'
//             }
//         ],
//         direction: 'left',
//         pad: {'r': 10, 't': 10},
//         showactive: true,
//         type: 'buttons',
//         x: 0.1,
//         xanchor: 'left',
//         y: 1.1,
//         yanchor: 'top'
//     }
// ]

// let annotations = [
//     {
//       text: 'View:',
//       x: 0,
//       y: 1.085,
//       yref: 'paper',
//       align: 'left',
//       showarrow: false
//     }
// ]

let layout = {
    // width: 800,
    // height: 900,
    autosize: true,
    margin: {t: 0, b: 0, l: 0, r: 0},
    // updatemenus: updatemenus,
    // annotations: annotations,
    scene: {camera: {projection: {type: 'orthographic'}}}
}

Plotly.newPlot('twisted_cubic_plot', [{type: 'scatter3d',
                                       mode: 'lines',
                                       x: x,
                                       y: y,
                                       z: z,
                                       layout: layout,
                                       opacity: 1,
                                       line: {width: 6, reversescale: false}}],
                layout, {displayModeBar: false});
