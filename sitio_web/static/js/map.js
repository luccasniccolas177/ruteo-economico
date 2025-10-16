// 1. Inicialización del Mapa
// Centramos el mapa en Santiago de Chile
const map = L.map('map').setView([-33.45, -70.65], 10);

// Capa base de OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// --- 2. Carga de Capas de Amenazas ---

// Función para añadir popups a cada amenaza
function onEachFeature(feature, layer) {
    if (feature.properties) {
        let popupContent = '<h4>' + (feature.properties.titulo || 'Amenaza') + '</h4>';
        for (const key in feature.properties) {
            popupContent += `<strong>${key}:</strong> ${feature.properties[key]}<br>`;
        }
        layer.bindPopup(popupContent);
    }
}

// Cargar Sismos
fetch('/static/amenazas/amenaza_sismos.geojson')
    .then(response => response.json())
    .then(data => {
        L.geoJSON(data, {
            onEachFeature: onEachFeature,
            pointToLayer: function (feature, latlng) {
                // Podríamos usar iconos diferentes aquí
                return L.marker(latlng);
            }
        }).addTo(map);
        console.log("Capa de sismos cargada.");
    });

// Cargar Incendios
fetch('/static/amenazas/amenaza_incendios.geojson')
    .then(response => response.json())
    .then(data => {
        L.geoJSON(data, {
            onEachFeature: onEachFeature,
            pointToLayer: function (feature, latlng) {
                // Icono rojo para incendios
                const redIcon = new L.Icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34]
                });
                return L.marker(latlng, { icon: redIcon });
            }
        }).addTo(map);
        console.log("Capa de incendios cargada.");
    });

// Cargar Inundaciones (Alertas)
fetch('/static/amenazas/amenaza_inundaciones.geojson')
    .then(response => response.json())
    .then(data => {
        L.geoJSON(data, {
            onEachFeature: onEachFeature,
            pointToLayer: function (feature, latlng) {
                // Icono azul para inundaciones
                 const blueIcon = new L.Icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34]
                });
                return L.marker(latlng, { icon: blueIcon });
            }
        }).addTo(map);
        console.log("Capa de inundaciones cargada.");
    });


// --- 3. Carga de la Ruta de Ejemplo (pgr_dijkstra) ---

fetch('/api/ruta_ejemplo')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error("Error al obtener la ruta:", data.error);
            return;
        }
        // Estilo para la línea de la ruta
        const routeStyle = {
            "color": "#ff7800",
            "weight": 5,
            "opacity": 0.65
        };
        L.geoJSON(data, { style: routeStyle }).addTo(map);
        console.log("Ruta de ejemplo cargada.");
    })
    .catch(error => console.error('Error fetching route:', error));