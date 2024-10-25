import './style.css';
import {Map, View} from 'ol';
//import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import ImageWMS from 'ol/source/ImageWMS.js';
import {Image as ImageLayer, Tile as TileLayer} from 'ol/layer.js';
import {fromLonLat, toLonLat, transform} from 'ol/proj.js';
import {toStringHDMS} from 'ol/coordinate.js';

const layers = [
  new TileLayer({source: new OSM()}),
  new ImageLayer({
    extent: [-5508658, -3356506, -5485284, -3324648],
    source: new ImageWMS({
      url: 'http://localhost:8080/geoserver/projeto_ygis/wms',
      params: {'LAYERS': 'projeto_ygis:ruas'},
      ratio: 1,
      serverType: 'geoserver'
    }),
  }),
];

const map = new Map({
  target: 'map',
  layers: layers,
  view: new View({
    center: [-5496028,-3335582],
    zoom: 10
  })
});

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
  const viewResolution = map.getView().getResolution();

  const url = `${wmsUrl}?${new URLSearchParams({
      ...featureRequestParams,
      BBOX: map.getView().calculateExtent(map.getSize()).toString(),
      WIDTH: map.getSize()[0],
      HEIGHT: map.getSize()[1],
      X: Math.floor(evt.pixel[0]),
      Y: Math.floor(evt.pixel[1]),
      SRS: 'EPSG:3857'
  }).toString()}`;

  fetch(url)
      .then((response) => response.json())
      .then((data) => {
          if (data.features.length > 0) {
              const attributes = data.features[0].properties;
              const tableHTML = createAttributesTable(attributes);
              document.getElementById('info').innerHTML = tableHTML;
          } else {
              document.getElementById('info').innerHTML = '<p>Nenhuma geometria encontrada.</p>';
          }
      })
      .catch((error) => console.log('Erro ao obter atributos:', error));

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

});


// Evento de movimentação do mouse no mapa
map.on('pointermove', function (evt) {
  const textCoord = getCoordinates(evt)
  
  // Exibir as coordenadas em um elemento específico
  document.getElementById('mouse-coordinates').innerHTML = `<p>Coordenadas: ${textCoord}</p>`;
});
  

