import './style.css';
import {Map, View} from 'ol';
//import TileLayer from 'ol/layer/Tile';
import OSM from 'ol/source/OSM';
import ImageWMS from 'ol/source/ImageWMS.js';
import {Image as ImageLayer, Tile as TileLayer} from 'ol/layer.js';
import {fromLonLat, toLonLat} from 'ol/proj.js';
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

// Função para lidar com cliques no mapa
map.on('singleclick', function (evt) {
  const coordinate = evt.coordinate;
  const hdms = toStringHDMS(toLonLat(coordinate));
  
  // Exibir as coordenadas no sidebar como exemplo
  document.getElementById('info').innerHTML = `<p>Coordenadas: ${hdms}</p>`;
});
