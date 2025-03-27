// to run node: npm start

import './style.css';
import {Map, View} from 'ol';
//import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import VectorTileLayer from 'ol/layer/VectorTile.js';
import VectorTileSource from 'ol/source/VectorTile.js';
import MVT from 'ol/format/MVT.js';
import ImageWMS from 'ol/source/ImageWMS.js';
import {Image as ImageLayer, Tile as TileLayer} from 'ol/layer.js';
import {fromLonLat, toLonLat, transform} from 'ol/proj.js';
import {toStringHDMS} from 'ol/coordinate.js';
import {Circle, Fill, Stroke, Style} from 'ol/style.js';

const layers = [
  new TileLayer({source: new OSM()}),
  // new ImageLayer({
  //   extent: [-5508658, -3356506, -5485284, -3324648],
  //   source: new ImageWMS({
  //     url: 'http://localhost:8080/geoserver/projeto_ygis/wms',
  //     params: {'LAYERS': 'projeto_ygis:ruas'},
  //     ratio: 1,
  //     serverType: 'geoserver'
  //   }),
  // }),
  new VectorTileLayer({
    declutter: false,
    source: new VectorTileSource({
      format: new MVT(),
      url: 'http://localhost:8081/vector-tiles/ruas/{z}/{x}/{y}.pbf'
    }),
    style: new Style({
        stroke: new Stroke({
          color: 'red',
          width: 1
        })
    })
  }),
  new VectorTileLayer({
    declutter: false,
    source: new VectorTileSource({
      format: new MVT(),
      url: 'http://localhost:8081/vector-tiles/escolas/{z}/{x}/{y}.pbf'
    }),
    style: new Style({
        image: new Circle({
          fill: new Fill({'color': 'rgba(0, 123, 255, 0.8)'}),
          radius: 6,
          stroke: new Stroke({'color': '#0056b3', 'width': 2})
        })
    })
  })
];

const map = new Map({
  target: 'map',
  layers: layers,
  view: new View({
    center: [-5496028,-3335582],
    zoom: 10
  })
});

// document.getElementById('resetPreference').addEventListener('click', () => {
//   localStorage.removeItem('showRoutingPopup'); //localStorage.setItem('showRoutingPopup', 'true'); //
//   alert('Popup preference reset. The popup will appear again next time.');
// });

const routeButton = document.getElementById('routeButton');
const resetPreferenceButton = document.getElementById('resetPreference');
const popup = document.getElementById('popup');
const overlay = document.getElementById('overlay');
const okButton = document.getElementById('okButton');
const dontShowAgainCheckbox = document.getElementById('dontShowAgain');
const mapContainer = document.getElementById('map');

// Function to check if the popup should be shown
function shouldShowPopup() {
  return localStorage.getItem('showRoutingPopup') !== 'false';
}

// Ensure the checkbox is unchecked by default
function resetCheckbox() {
  dontShowAgainCheckbox.checked = false;
}

let routeMode = false; // Flag to enable/disable route selection mode
let point1 = null;
let point2 = null;

// Show the popup when the route button is clicked, if allowed
routeButton.addEventListener('click', () => {
  routeMode = true;
  point1 = null;
  point2 = null;

  mapContainer.style.cursor = 'crosshair';

  if (shouldShowPopup()) {
      popup.style.display = 'block';
      overlay.style.display = 'block';
  }
});

// Hide the popup when the OK button is clicked
okButton.addEventListener('click', () => {
  popup.style.display = 'none';
  overlay.style.display = 'none';

  // Save the user's preference in local storage
  if (dontShowAgainCheckbox.checked) {
      localStorage.setItem('showRoutingPopup', 'false');
  }
});

// Reset the popup preference and uncheck the checkbox
resetPreferenceButton.addEventListener('click', () => {
  localStorage.removeItem('showRoutingPopup'); // Reset the preference
  resetCheckbox(); // Uncheck the checkbox
  alert('Popup preference reset. The popup will appear again next time.');
});

// Initialize the checkbox state
resetCheckbox();

// URL do WMS (substitua com a URL do seu servidor GeoServer)
const wmsUrl = 'http://localhost:8080/geoserver/projeto_ygis/wms';

// Parâmetros da requisição GetFeatureInfo
const featureRequestParams = {
    REQUEST: 'GetFeatureInfo',
    SERVICE: 'WMS',
    VERSION: '1.1.1',
    LAYERS: 'projeto_ygis:ruas',
    QUERY_LAYERS: 'projeto_ygis:ruas',
    INFO_FORMAT: 'application/json', // Formato da resposta
    FEATURE_COUNT: 1 // Quantidade máxima de feições retornadas
};

// Função para converter atributos JSON em uma tabela HTML
function createAttributesTable(attributes) {
  let table = '<table border="1" cellpadding="5" cellspacing="0" style="width:100%;">';
  table += '<thead><tr><th>Campo</th><th>Valor</th></tr></thead><tbody>';
  
  for (const [key, value] of Object.entries(attributes)) {
      table += `<tr><td>${key}</td><td>${value}</td></tr>`;
  }
  
  table += '</tbody></table>';
  return table;
}

function getCoordinates(event) {
  var coordinate = event.coordinate;
  //const hdms = toStringHDMS(toLonLat(coordinate));
  var pointCoord = transform(coordinate, 'EPSG:3857', 'EPSG:4326')
  var textCoord = `${pointCoord[0].toFixed(6)}; ${pointCoord[1].toFixed(6)} `
  
  return textCoord;
}

// Evento de clique no mapa para obter atributos
map.on('singleclick', function (evt) {
  // const viewResolution = map.getView().getResolution();

  // const url = `${wmsUrl}?${new URLSearchParams({
  //     ...featureRequestParams,
  //     BBOX: map.getView().calculateExtent(map.getSize()).toString(),
  //     WIDTH: map.getSize()[0],
  //     HEIGHT: map.getSize()[1],
  //     X: Math.floor(evt.pixel[0]),
  //     Y: Math.floor(evt.pixel[1]),
  //     SRS: 'EPSG:3857'
  // }).toString()}`;

  // fetch(url)
  //     .then((response) => response.json())
  //     .then((data) => {
  //         if (data.features.length > 0) {
  //             const attributes = data.features[0].properties;
  //             const tableHTML = createAttributesTable(attributes);
  //             document.getElementById('info').innerHTML = tableHTML;
  //         } else {
  //             document.getElementById('info').innerHTML = '<p>Nenhuma geometria encontrada.</p>';
  //         }
  //     })
  //     .catch((error) => console.log('Erro ao obter atributos:', error));

  // Caso o usuário clique segurando a tecla Ctrl.
  const originalEvent = evt.originalEvent;
  if (originalEvent.ctrlKey == true) {
    const textCoord = getCoordinates(evt)
    navigator.clipboard.writeText(textCoord);

    const messageElement = document.getElementById('copy-coordinates')
    messageElement.innerHTML = `<p>As coordenadas foram copiadas na área de transferência.</p>`
    messageElement.classList.add('fade-out');

    setTimeout(() => {
      messageElement.classList.add("hidden");
    }, 1000)

    setTimeout(() => {
      messageElement.innerHTML = "";
      messageElement.classList.remove("hidden", "fade-out");
    }, 5000);
  }
  if (routeMode) {
    const coordinate = evt.coordinate;
    if (!point1) {
        point1 = coordinate;
        alert('First point selected. Click again to select the second point.');
    } else if (!point2) {
        point2 = coordinate;
        routeMode = false; // Disable route selection mode
        alert('Second point selected. Calculating route...');
        mapContainer.style.cursor = 'default';
        //sendCoordinatesToBackend(point1, point2); // Send coordinates to backend
    }
  }

  else {
    const coordinate = evt.coordinate;
    const [lon, lat] = toLonLat(coordinate);

    const url = `http://localhost:8081/data/ruas?lat=${lat}&lon=${lon}`;

    fetch(url)
      .then(response => response.json())
      .then(data => {
                if (data.length > 0) {
                    const attributes = data[0];
                    const tableHTML = createAttributesTable(attributes);
                    document.getElementById('info').innerHTML = tableHTML;
                } else {
                    document.getElementById('info').innerHTML = '<b style=\'color:red;\'><p>Nenhuma geometria encontrada.</p></b>';
                }
            })
      .catch(error => console.error('Ah, erro!', error));    
  }
});


// Evento de movimentação do mouse no mapa
map.on('pointermove', function (evt) {
  const textCoord = getCoordinates(evt)
  
  // Exibir as coordenadas em um elemento específico
  document.getElementById('mouse-coordinates').innerHTML = `<p>Coordenadas: ${textCoord}</p>`;
});
  

