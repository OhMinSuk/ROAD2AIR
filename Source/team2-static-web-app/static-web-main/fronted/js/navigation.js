let TMAP_API_KEY = "";
let KAKAO_JAVASCRIPT_KEY = "";
let KAKAO_MAPS_REST_API = "";

async function loadApiKeys() {
    try {
        const response = await fetch("/api/navigation");
        if (!response.ok) throw new Error("API 호출 실패");

        const config = await response.json();
        TMAP_API_KEY = config.TMAP_API_KEY;
        KAKAO_JAVASCRIPT_KEY = config.KAKAO_JAVASCRIPT_KEY;
        KAKAO_MAPS_REST_API = config.KAKAO_MAPS_REST_API;

        console.log("API 키 로드 완료");
        initializeKakao(); // 여기서 호출됨
    } catch (err) {
        console.error("API 키 불러오기 실패:", err);
    }
}

// 페이지 로드시 실행
document.addEventListener('DOMContentLoaded', loadApiKeys);

function initializeKakao() {
    // KAKAO_JAVASCRIPT_KEY가 로드되었는지 확인
    if (!KAKAO_JAVASCRIPT_KEY) {
        console.error("카카오 JavaScript API 키가 없습니다.");
        return;
    }

    // 카카오맵 SDK 로드 (loadKakaoMapSdk 함수를 재활용하거나 직접 로직 구현)
    // navigation.js에 이미 loadKakaoMapSdk 함수가 있으므로, 이를 활용합니다.
    loadKakaoMapSdk(() => {
        console.log("카카오맵 SDK 로드 및 초기화 완료");
        // 초기 맵 렌더링 또는 필요한 추가 초기화 로직
        // 예: setLocation(기본_위도, 기본_경도, '기본'); // 초기 위치 설정 함수가 있다면 호출
        // updateAirportMap(); // 공항 지도 업데이트
        // updateFacilityListWithRoutes(); // 시설 목록 업데이트
        getCurrentLocation(); // 현재 위치를 자동으로 가져오는 함수를 호출
    });
}

// 전역 변수로 각 시설별 경로 정보 캐시
let facilityRouteCache = new Map();

function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

function fetchCarRoute(userLat, userLng, terminal, callback) {
    const url = `https://apis-navi.kakaomobility.com/v1/directions?origin=${userLng},${userLat}&destination=${terminal.lng},${terminal.lat}&priority=RECOMMEND`;

    fetch(url, {
        headers: {
            Authorization: 'KakaoAK ' + KAKAO_MAPS_REST_API
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.routes && data.routes.length > 0) {
            const summary = data.routes[0].summary;
            const routeInfo = {
                duration: Math.round(summary.duration / 60), // 분 단위
                distance: (summary.distance / 1000).toFixed(1), // km 단위
                taxiFare: summary.fare.taxi,
                toll: summary.fare.toll
            };
            callback(routeInfo);
        } else {
            callback(null);
        }
    })
    .catch(error => {
        console.error('API 호출 실패:', error);
        callback(null);
    });
}

function generateTerminalRoutes(userLat, userLng) {
    const routes = [];
    let completedRequests = 0;
    const totalTerminals = Object.keys(airportTerminals).length;

    return new Promise((resolve) => {
        // 터미널 정렬 (1터미널이 먼저 오도록)
        const sortedTerminals = Object.values(airportTerminals).sort((a, b) => {
            const aName = a.name[currentLang] || a.name.ko;
            const bName = b.name[currentLang] || b.name.ko;
            return aName.localeCompare(bName);
        });

        // 각 터미널의 인덱스를 저장할 배열 생성
        const terminalRoutes = new Array(sortedTerminals.length);

        sortedTerminals.forEach((terminal, index) => {
            fetchCarRoute(userLat, userLng, terminal, (routeInfo) => {
                const terminalName = terminal.name[currentLang] || terminal.name.ko;
                const stationName = terminal.stationName[currentLang] || terminal.stationName.ko;
                
                // 해당 터미널의 경로들을 배열에 저장
                terminalRoutes[index] = [];

                // 자동차 경로 추가
                if (routeInfo) {
                    // API 데이터 사용
                    const totalTaxiFare = routeInfo.taxiFare + routeInfo.toll;
                    terminalRoutes[index].push({
                        type: `🚗 ${translations[currentLang]['car_to_terminal']} ${terminalName}`,
                        duration: `${routeInfo.duration}${translations[currentLang]['minutes']}`,
                        description: `${translations[currentLang]['current_location']} → ${stationName}`,
                        cost: `${translations[currentLang]['taxi_fare']} ${totalTaxiFare.toLocaleString()}${translations[currentLang]['currency']}`,
                        interval: `${translations[currentLang]['real_time_traffic']} | ${routeInfo.distance}km`,
                        kakaoUrl: `https://map.kakao.com/link/to/${terminalName},${terminal.lat},${terminal.lng}/from/${translations[currentLang]['current_location']},${userLat},${userLng}`
                    });
                } else {
                    // API 실패 시 기본 정보만 제공
                    terminalRoutes[index].push({
                        type: `🚗 ${translations[currentLang]['car_to_terminal']} ${terminalName}`,
                        duration: `${translations[currentLang]['minutes']}`,
                        description: `${translations[currentLang]['current_location']} → ${stationName}`,
                        cost: `${translations[currentLang]['taxi_fare']}`,
                        interval: translations[currentLang]['real_time_traffic'],
                        kakaoUrl: `https://map.kakao.com/link/to/${terminalName},${terminal.lat},${terminal.lng}/from/${translations[currentLang]['current_location']},${userLat},${userLng}`
                    });
                }

                // 대중교통 경로 추가 (각 터미널별로)
                const busKey = terminalName.includes('1') ? 'airport_bus' : 'airport_bus2';
                const routeKey = terminalName.includes('1') ? 'airport_bus_route' : 'airport_bus_route2';
                
                terminalRoutes[index].push({
                    type: `🚌 ${translations[currentLang][busKey]}`,
                    duration: '',
                    description: translations[currentLang][routeKey],
                    cost: '',
                    interval: translations[currentLang]['transit_api_notice'] || '현재 카카오 API에서는 대중교통 정보를 제공하지 않습니다. 아래의 카카오맵으로 이동 후 🚌 버스 아이콘을 클릭하십시오',
                    kakaoUrl: `https://map.kakao.com/link/to/${terminalName},${terminal.lat},${terminal.lng}/from/${translations[currentLang]['current_location']},${userLat},${userLng}?target=transit`
                });

                completedRequests++;
                if (completedRequests === totalTerminals) {
                    // 모든 요청이 완료되면 차량 경로 먼저, 버스 경로 나중에 추가
                    
                    // 1. 차량 경로들 먼저 추가 (터미널 순서대로)
                    terminalRoutes.forEach(terminalRouteArray => {
                        if (terminalRouteArray && terminalRouteArray[0]) {
                            routes.push(terminalRouteArray[0]); // 차량 경로 (첫 번째 요소)
                        }
                    });
                    
                    // 2. 버스 경로들 나중에 추가 (터미널 순서대로)
                    terminalRoutes.forEach(terminalRouteArray => {
                        if (terminalRouteArray && terminalRouteArray[1]) {
                            routes.push(terminalRouteArray[1]); // 버스 경로 (두 번째 요소)
                        }
                    });
                    
                    resolve(routes);
                }
            });
        });
    });
}

// getRouteToAirport 함수는 변경사항 없음
function getRouteToAirport() {
    const statusDiv = document.getElementById('route-status');
    const infoDiv = document.getElementById('route-info');
    
    statusDiv.innerHTML = `<div class="loading"><div class="spinner"></div>${translations[currentLang]['route_loading']}</div>`;
    infoDiv.innerHTML = '';

    if (!navigator.geolocation) {
        statusDiv.innerHTML = `<div class="status error"><i class="fas fa-exclamation-circle"></i> ${translations[currentLang]['route_unsupported']}</div>`;
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function(position) {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;
            
            // 직선거리 계산 제거하고 단순히 위치 확인 성공 메시지만 표시
            statusDiv.innerHTML = `<div class="status success"><i class="fas fa-check-circle"></i> ${translations[currentLang]['route_location_success']}</div>`;
            
            // 터미널별 경로 생성 (비동기)
            generateTerminalRoutes(userLat, userLng).then(terminalRoutes => {
                let content = `<div class="info-card">
                    <h3><i class="fas fa-road"></i> ${translations[currentLang]['recommended_transport']}</h3>
                    <div class="transit-routes">`;
                
                terminalRoutes.forEach(route => {
                    const buttonHtml = route.kakaoUrl ? 
                        `<a href="${route.kakaoUrl}" target="_blank" class="btn" style="background: #FEE500; color: #3A1D1D; font-weight: bold; text-decoration: none; display: inline-block; padding: 8px 15px; border-radius: 6px; font-size: 12px; margin-top: 8px;">
                            <i class="fas fa-map-marked-alt"></i> ${translations[currentLang]['view_in_kakaomap']}
                        </a>` : '';
                    
                    content += `
                        <div class="transit-route" style="background: #f8f9fa; border-radius: 12px; padding: 15px; margin: 10px 0; border-left: 4px solid var(--main-teal);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <span style="font-weight: 700; color: var(--sub-deep-blue);">${route.type}</span>
                                <span style="font-weight: 700; color: var(--main-teal);">${route.duration}</span>
                            </div>
                            <div style="font-size: 14px; color: #666; margin-bottom: 8px;">${route.description}</div>
                            <div style="font-size: 13px; color: #888;">
                                ${route.cost ? `${route.cost}` : ''}
                                ${route.cost && route.interval ? ' | ' : ''}
                                ${route.interval ? `${route.interval}` : ''}
                            </div>
                            ${buttonHtml}
                        </div>
                    `;
                });
                
                content += `</div></div>`;
                infoDiv.innerHTML = content;
            });
        },
        function(error) {
            statusDiv.innerHTML = `<div class="status error"><i class="fas fa-exclamation-circle"></i> ${translations[currentLang]['route_location_error']}</div>`;
        }
    );
}

window.setLocation = function(lat, lng, type = '수동') {
    currentLocation = { lat, lng };

    facilityRouteCache.clear();

    const statusDiv = document.getElementById('location-status');
    const typeText = translations[currentLang][`${type.toLowerCase()}_location_type`] || type;
    statusDiv.innerHTML = `<div class="status success"><i class="fas fa-check-circle"></i> ${translations[currentLang]['set_location_success'].replace('{type}', typeText)}</div>`;

    loadKakaoMapSdk(() => {
        updateAirportMap();
        updateFacilityListWithRoutes();
    });
};

function getCurrentLocation() {
    const statusDiv = document.getElementById('location-status');
    if (!navigator.geolocation) {
        statusDiv.innerHTML = `<div class="status error"><i class="fas fa-exclamation-circle"></i> ${translations[currentLang]['route_unsupported']}</div>`;
        return;
    }
    statusDiv.innerHTML = `<div class="loading"><div class="spinner"></div>${translations[currentLang]['route_loading']}</div>`;
    navigator.geolocation.getCurrentPosition(
        position => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            if (isInsideAirport(lat, lng)) {
                setLocation(lat, lng, 'GPS');
            } else {
                currentLocation = null;
                window.selectedFacility = null;
                facilityRouteCache.clear();
                
                const routeInfoDiv = document.getElementById('route-info-display');
                if (routeInfoDiv) {
                    routeInfoDiv.innerHTML = '';
                }

                if (window.currentPolyline) {
                    window.currentPolyline.setMap(null);
                    window.currentPolyline = null;
                }
                if (window.currentDestMarker) {
                    window.currentDestMarker.setMap(null);
                    window.currentDestMarker = null;
                }
                
                updateFacilityListWithRoutes();
                
                const mapDiv = document.getElementById('airport-map');
                mapDiv.innerHTML = `
                    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #e74c3c; font-size: 18px; font-weight: bold;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 20px;"></i>
                        ${translations[currentLang]['outside_airport_warning']}
                    </div>
                `;
                statusDiv.innerHTML = `<div class="status error"><i class="fas fa-exclamation-circle"></i> ${translations[currentLang]['outside_airport_warning']}</div>`;
            }
        },
        () => statusDiv.innerHTML = `<div class="status error"><i class="fas fa-exclamation-circle"></i> ${translations[currentLang]['set_location_error']}</div>`
    );
}

document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        const tabName = this.getAttribute('data-tab');
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        this.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');
    });
});

function loadKakaoMapSdk(callback) {
    if (window.kakao && window.kakao.maps) {
        callback();
        return;
    }

    const script = document.createElement('script');
    script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_JAVASCRIPT_KEY}&autoload=false`;
    script.onload = () => {
        kakao.maps.load(callback);
    };
    document.head.appendChild(script);
}

function isInsideAirport(lat, lng) {
    const airportCenter = { lat: 37.4602, lng: 126.4407 };
    const distance = calculateDistance(lat, lng, airportCenter.lat, airportCenter.lng);
    return distance <= 5;
}

function updateAirportMap() {
    const mapDiv = document.getElementById('airport-map');
    if (!currentLocation) return;

    mapDiv.innerHTML = '';

    currentMap = new kakao.maps.Map(mapDiv, {
        center: new kakao.maps.LatLng(currentLocation.lat, currentLocation.lng),
        level: 3
    });

    const userMarkerImage = new kakao.maps.MarkerImage(
        'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/markerStar.png',
        new kakao.maps.Size(24, 35)
    );
    
    const userMarker = new kakao.maps.Marker({
        position: new kakao.maps.LatLng(currentLocation.lat, currentLocation.lng),
        map: currentMap,
        image: userMarkerImage,
        zIndex: 1
    });

    const legend = document.createElement('div');
    legend.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        background: white;
        border: 2px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        font-size: 12px;
        font-weight: bold;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        z-index: 1000;
    `;

    legend.innerHTML = `
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 12px; height: 12px; background: #FFD700; border-radius: 50%; margin-right: 8px;"></div>
            <span style="color: #01AAB5;">${translations[currentLang]['current_location_text'] || '현재 위치'}</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 12px; height: 12px; background: #238CFA; border-radius: 50%; margin-right: 8px;"></div>
            <span style="color: #666;">${translations[currentLang]['nearby_facilities'] || '주변 시설'}</span>
        </div>
    `;

    mapDiv.style.position = 'relative';
    mapDiv.appendChild(legend);

    airportFacilities.forEach(facility => {
        const distance = getDistance(currentLocation.lat, currentLocation.lng, facility.lat, facility.lng);
        if (distance > 0) {
            const marker = new kakao.maps.Marker({
                position: new kakao.maps.LatLng(facility.lat, facility.lng),
                map: currentMap
            });

            const infoWindow = new kakao.maps.InfoWindow({
                content: `<div style="padding:5px; font-size:12px; font-weight:600; min-width:120px;">${facility.name[currentLang] || facility.name.ko}</div>`
            });

            kakao.maps.event.addListener(marker, 'click', function() {
                if (currentInfoWindow) {
                    currentInfoWindow.close();
                }
                
                infoWindow.open(currentMap, marker);
                currentInfoWindow = infoWindow;
            });
        }
    });
}

function getTmapWalkingRoute(startLat, startLng, endLat, endLng, callback) {
    if (!TMAP_API_KEY || TMAP_API_KEY.trim() === '') {
        console.error('T-map API 키가 설정되지 않았습니다.');
        callback(null);
        return;
    }

    const url = 'https://apis.openapi.sk.com/tmap/routes/pedestrian';
    
    const requestData = {
        startX: startLng,
        startY: startLat,
        endX: endLng,
        endY: endLat,
        reqCoordType: 'WGS84GEO',
        resCoordType: 'WGS84GEO',
        startName: '출발지',
        endName: '도착지'
    };

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'appKey': TMAP_API_KEY
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.features && data.features.length > 0) {
            const routeData = processTmapRouteData(data);
            callback(routeData);
        } else {
            console.error('T-map API 응답 오류:', data);
            callback(null);
        }
    })
    .catch(error => {
        // console.error('T-map API 호출 실패:', error);
        callback(null);
    });
}

function processTmapRouteData(data) {
    const coordinates = [];
    let totalDistance = 0;
    let totalTime = 0;

    data.features.forEach(feature => {
        if (feature.geometry.type === 'LineString') {
            feature.geometry.coordinates.forEach(coord => {
                coordinates.push(new kakao.maps.LatLng(coord[1], coord[0]));
            });
        } else if (feature.geometry.type === 'Point') {
            coordinates.push(new kakao.maps.LatLng(
                feature.geometry.coordinates[1], 
                feature.geometry.coordinates[0]
            ));
        }

        if (feature.properties) {
            if (feature.properties.distance) {
                totalDistance += feature.properties.distance;
            }
            if (feature.properties.time) {
                totalTime += feature.properties.time;
            }
        }
    });

    const lastFeature = data.features[data.features.length - 1];
    if (lastFeature && lastFeature.properties) {
        totalDistance = lastFeature.properties.totalDistance || totalDistance;
        totalTime = lastFeature.properties.totalTime || totalTime;
    }

    return {
        coordinates: coordinates,
        distance: totalDistance,
        duration: totalTime,
        isFromTmap: true
    };
}

function getDistance(lat1, lng1, lat2, lng2) {
    const R = 6371e3;
    const toRad = deg => deg * Math.PI / 180;

    const φ1 = toRad(lat1);
    const φ2 = toRad(lat2);
    const Δφ = toRad(lat2 - lat1);
    const Δλ = toRad(lng2 - lng1);

    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
}

// 시설 목록을 T-map API로 업데이트하는 새로운 함수
function updateFacilityListWithRoutes() {
    const facilityDiv = document.getElementById('facility-list');
    if (!currentLocation) {
        facilityDiv.innerHTML = `<p style="text-align: center; color: #666;">${translations[currentLang]['please_set_location']}</p>`;
        return;
    }
    
    // 현재 위치에서 1m 이내인 시설들 필터링 (현재 위치 시설은 목록에서 제외)
    const facilitiesWithDistance = airportFacilities.filter(facility => {
        const distance = calculateDistance(currentLocation.lat, currentLocation.lng, facility.lat, facility.lng);
        return distance >= 0.001; // 1m 이상인 시설만 표시
    }).map(facility => ({
        ...facility,
        distance: calculateDistance(currentLocation.lat, currentLocation.lng, facility.lat, facility.lng),
        routeStatus: 'loading' // 초기 상태
    })).sort((a, b) => a.distance - b.distance).slice(0, 10); // 상위 10개만 선택
    
    // 로딩 상태로 먼저 렌더링
    facilityDiv.innerHTML = facilitiesWithDistance.map((facility, index) => {
        return `
            <div class="facility-item" data-facility-index="${index}">
                <h4>${facility.name[currentLang] || facility.name.ko}</h4>
                <p>${facility.description[currentLang] || facility.description.ko}</p>
                <div class="distance-info loading-route">
                    <div class="loading-mini">
                        <div class="spinner-mini"></div>
                        ${translations[currentLang]['route_loading'] || '경로 확인 중...'}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // 각 시설에 대해 T-map API 호출
    facilitiesWithDistance.forEach((facility, index) => {
        const cacheKey = `${facility.lat},${facility.lng}`;
        
        if (facilityRouteCache.has(cacheKey)) {
            // 캐시된 데이터 사용
            const cachedRoute = facilityRouteCache.get(cacheKey);
            updateFacilityItemDisplay(index, facility, cachedRoute);
        } else {
            // T-map API 호출
            getTmapWalkingRoute(
                currentLocation.lat, 
                currentLocation.lng, 
                facility.lat, 
                facility.lng, 
                function(routeData) {
                    // 결과를 캐시에 저장
                    facilityRouteCache.set(cacheKey, routeData);
                    updateFacilityItemDisplay(index, facility, routeData);
                }
            );
        }
    });
    
    window.facilitiesWithDistance = facilitiesWithDistance;
}

// 개별 시설 항목 표시 업데이트
function updateFacilityItemDisplay(index, facility, routeData) {
    const facilityItem = document.querySelector(`[data-facility-index="${index}"]`);
    if (!facilityItem) return;

    const distanceInfo = facilityItem.querySelector('.distance-info');
    
    if (routeData && routeData.isFromTmap) {
        // T-map API 성공 - 정확한 도보 경로 정보 표시
        const distance = routeData.distance < 1000 
            ? `${Math.round(routeData.distance)}m`
            : `${(routeData.distance / 1000).toFixed(1)}km`;
        
        const walkingTime = Math.round(routeData.duration / 60);
        
        distanceInfo.innerHTML = `
            <i class="fas fa-walking"></i> 
            ${distance} • ${translations[currentLang]['walking_time'].replace('{time}', walkingTime)}
        `;
        distanceInfo.classList.remove('loading-route');
        facilityItem.classList.add('walkable');
        facilityItem.setAttribute('onclick', `showFacilityRoute(${index})`);
        facilityItem.style.cursor = 'pointer';
        
        // 시설 데이터에 경로 정보 추가
        window.facilitiesWithDistance[index].routeData = routeData;
        window.facilitiesWithDistance[index].routeStatus = 'success';
        
    } else {
        // T-map API 실패 - 도보 불가 표시
        distanceInfo.innerHTML = `
            <i class="fas fa-ban" style="color: #e74c3c;"></i>
            <span style="color: #e74c3c;">${translations[currentLang]['walking_not_available'] || '도보 불가'}</span>
        `;
        distanceInfo.classList.remove('loading-route');
        facilityItem.classList.add('not-walkable');
        facilityItem.style.cursor = 'not-allowed';
        facilityItem.style.opacity = '0.7';
        
        window.facilitiesWithDistance[index].routeStatus = 'failed';
    }
}

function showFacilityRoute(facilityIndex) {
    if (!currentLocation || !window.facilitiesWithDistance) return;
    
    const facility = window.facilitiesWithDistance[facilityIndex];
    
    // 도보 불가능한 시설인 경우 처리하지 않음
    if (facility.routeStatus === 'failed') {
        return;
    }
    
    window.selectedFacility = facility;
    
    const routeInfoDiv = document.getElementById('route-info-display') || createRouteInfoDisplay();
    const facilityName = facility.name[currentLang] || facility.name.ko;
    
    // 이미 경로 데이터가 있는 경우 바로 표시
    if (facility.routeData && facility.routeData.isFromTmap) {
        displayRouteOnMap(facility, facility.routeData);
        updateRouteInfoDisplay(facility, facility.routeData);
    } else {
        // 로딩 상태 표시
        routeInfoDiv.innerHTML = `
            <div class="route-info-card" style="background: linear-gradient(135deg, #01AAB5, #006EEA); color: white; padding: 15px; border-radius: 12px; margin: 15px 0;">
                <div style="display: flex; align-items: center; justify-content: center;">
                    <div class="loading" style="color: white;">
                        <div class="spinner" style="border-left-color: white;"></div>
                        ${translations[currentLang]['route_loading']}
                    </div>
                </div>
            </div>
        `;
        
        // T-map API 재호출
        getTmapWalkingRoute(
            currentLocation.lat, 
            currentLocation.lng, 
            facility.lat, 
            facility.lng, 
            function(routeData) {
                if (routeData && routeData.coordinates && currentMap) {
                    displayRouteOnMap(facility, routeData);
                    updateRouteInfoDisplay(facility, routeData);
                } else {
                    showWalkingNotAvailable(facility);
                }
            }
        );
    }
}

// 지도에 경로 표시하는 함수
function displayRouteOnMap(facility, routeData) {
    if (!currentMap || !routeData.coordinates) return;
    
    const polyline = new kakao.maps.Polyline({
        path: routeData.coordinates,
        strokeWeight: 5,
        strokeColor: '#01AAB5',
        strokeOpacity: 0.8,
        strokeStyle: 'solid'
    });
    
    if (window.currentPolyline) {
        window.currentPolyline.setMap(null);
    }
    
    polyline.setMap(currentMap);
    window.currentPolyline = polyline;
    
    if (window.currentDestMarker) {
        window.currentDestMarker.setMap(null);
    }
    
    const destMarker = new kakao.maps.Marker({
        position: new kakao.maps.LatLng(facility.lat, facility.lng),
        map: currentMap
    });
    window.currentDestMarker = destMarker;
    
    window.currentRouteInfo = routeData;
    
    const bounds = new kakao.maps.LatLngBounds();
    routeData.coordinates.forEach(coord => bounds.extend(coord));
    currentMap.setBounds(bounds);
}

// 도보 이용 불가 메시지 표시 함수
function showWalkingNotAvailable(facility) {
    const routeInfoDiv = document.getElementById('route-info-display');
    if (!routeInfoDiv) return;
    
    const facilityName = facility.name[currentLang] || facility.name.ko;
    const facilityDescription = facility.description[currentLang] || facility.description.ko;
    
    routeInfoDiv.innerHTML = `
        <div class="route-info-card" style="background: linear-gradient(135deg, #E74C3C, #C0392B); color: white; padding: 15px; border-radius: 12px; margin: 15px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: white;">
                        <i class="fas fa-exclamation-triangle"></i> ${translations[currentLang]['walking_not_available'] || '도보로 갈 수 없습니다'}
                    </h4>
                    <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 16px; font-weight: 500;">${facilityName}</p>
                    <p style="margin: 5px 0 0 0; opacity: 0.8; font-size: 14px;">${facilityDescription}</p>
                    <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 13px;">
                        <i class="fas fa-info-circle"></i> ${translations[currentLang]['walking_not_available_desc'] || '공항 셔틀버스나 다른 교통수단을 이용해주세요'}
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 32px; opacity: 0.7;">
                        <i class="fas fa-ban"></i>
                    </div>
                </div>
            </div>
            <div style="margin-top: 10px; display: flex; gap: 10px;">
                <button onclick="clearRoute()" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 5px 10px; border-radius: 6px; cursor: pointer;">
                    <i class="fas fa-times"></i> ${translations[currentLang]['clear_route']}
                </button>
                <button onclick="openKakaoMapRoute(currentLocation, window.selectedFacility, '${facilityName}')" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 5px 10px; border-radius: 6px; cursor: pointer;">
                    <i class="fas fa-external-link-alt"></i> ${translations[currentLang]['view_in_kakaomap']}
                </button>
            </div>
        </div>
    `;
    
    if (window.currentPolyline) {
        window.currentPolyline.setMap(null);
        window.currentPolyline = null;
    }
    
    if (window.currentDestMarker) {
        window.currentDestMarker.setMap(null);
        window.currentDestMarker = null;
    }
}

// 경로 정보 업데이트 함수 (T-map API 성공 시)
function updateRouteInfoDisplay(facility, routeData) {
    const routeInfoDiv = document.getElementById('route-info-display');
    if (!routeInfoDiv) return;
    
    const facilityName = facility.name[currentLang] || facility.name.ko;
    const facilityDescription = facility.description[currentLang] || facility.description.ko;
    
    const distance = routeData.distance < 1000 
        ? `${Math.round(routeData.distance)}m`
        : `${(routeData.distance / 1000).toFixed(1)}km`;
    
    const walkingTime = Math.round(routeData.duration / 60);
    const arrivalMessage = translations[currentLang]['arrived_to'].replace('{name}', facilityName);
    
    routeInfoDiv.innerHTML = `
        <div class="route-info-card" style="background: linear-gradient(135deg, #01AAB5, #006EEA); color: white; padding: 15px; border-radius: 12px; margin: 15px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0; color: white;"><i class="fas fa-walking"></i> ${arrivalMessage}</h4>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">${facilityDescription}</p>
                    <p style="margin: 5px 0 0 0; opacity: 0.8; font-size: 12px;">
                        <i class="fas fa-route"></i> ${translations[currentLang]['tmap_route_info'] || 'T-map 경로 정보'}
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 18px; font-weight: bold;">${distance}</div>
                    <div style="font-size: 14px; opacity: 0.9;">${translations[currentLang]['walking_time'].replace('{time}', walkingTime)}</div>
                </div>
            </div>
            <div style="margin-top: 10px; display: flex; gap: 10px;">
                <button onclick="clearRoute()" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 5px 10px; border-radius: 6px; cursor: pointer;">
                    <i class="fas fa-times"></i> ${translations[currentLang]['clear_route']}
                </button>
                <button onclick="openKakaoMapRoute(currentLocation, window.selectedFacility, '${facilityName}')" style="background: rgba(255,255,255,0.2); border: none; color: white; padding: 5px 10px; border-radius: 6px; cursor: pointer;">
                    <i class="fas fa-external-link-alt"></i> ${translations[currentLang]['view_in_kakaomap']}
                </button>
            </div>
        </div>
    `;
}

// 경로 정보 표시 영역 생성
function createRouteInfoDisplay() {
    const routeInfoDiv = document.createElement('div');
    routeInfoDiv.id = 'route-info-display';
    
    const mapContainer = document.querySelector('.map-container');
    mapContainer.parentNode.insertBefore(routeInfoDiv, mapContainer);
    
    return routeInfoDiv;
}

// 경로 지우기 함수
function clearRoute() {
    window.selectedFacility = null;
    
    const routeInfoDiv = document.getElementById('route-info-display');
    if (routeInfoDiv) {
        routeInfoDiv.innerHTML = '';
    }
    
    if (window.currentPolyline && currentMap) {
        window.currentPolyline.setMap(null);
        window.currentPolyline = null;
    }
    
    if (window.currentDestMarker && currentMap) {
        window.currentDestMarker.setMap(null);
        window.currentDestMarker = null;
    }
    
    updateAirportMap();
}

// 카카오맵에서 경로 보기 함수


function openKakaoMapRoute(start, end, endName) {
    // 출발지 (현재 위치) 정보를 URL에 포함하여 경로를 요청
    // Kakao Map Link API의 경로 찾기 URL 형식:
    // kakao.com/link/to/목적지이름,목적지위도,목적지경도?f=출발지이름,출발지위도,출발지경도
    const startName = translations[currentLang]['current_location_text'] || '현재 위치'; // '현재 위치'를 다국어 처리
    const url = `https://map.kakao.com/link/to/${encodeURIComponent(endName)},${end.lat},${end.lng}/from/${encodeURIComponent(startName)},${start.lat},${start.lng}`;
    window.open(url, '_blank');
}

// 기존 updateFacilityList 함수를 새로운 함수로 대체
function updateFacilityList() {
    updateFacilityListWithRoutes();
}
