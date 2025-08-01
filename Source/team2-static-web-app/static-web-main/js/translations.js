// 통합된 다국어 번역 객체
const translations = {
    'ko': {
        // 헤더
        'header_title': '인천공항 네비게이션',
        'header_subtitle': '스마트한 공항 안내 시스템',
        
        // 탭 메뉴
        'route_tab_text': '공항 가는 길',
        'airport_tab_text': '공항 내 안내',
        
        // 공항 가는 길 섹션
        'route_heading': '인천공항까지 최적 경로',
        'route_description': '현재 위치를 기반으로 인천공항까지의 차량 및 교통편 거리와 소요 시간을 안내해 드립니다.',
        'find_route_btn': '현재 위치에서 길찾기',
        'route_loading': '현재 위치를 확인하고 있습니다...',
        'route_unsupported': '위치 서비스를 지원하지 않는 브라우저입니다.',
        'route_location_success': '위치 확인 완료!',
        'route_location_error': '위치 정보를 가져올 수 없습니다. 위치 서비스를 활성화해주세요.',
        
        // 교통편 정보
        'recommended_transport': '추천 교통편',
        'car_to_terminal': '자동차 →',
        'taxi_fare': '택시비: 약',
        'minutes': '분',
        'currency': '원',
        'real_time_traffic': '실시간 교통상황 반영',
        'airport_bus': '대중교통으로 인천국제공항 제1터미널',
        'airport_bus2': '대중교통으로 인천국제공항 제2터미널',
        'airport_bus_route': '현재 위치 → 인천공항 1터미널역',
        'airport_bus_route2': '현재 위치 → 인천공항 2터미널역',
        'transit_api_notice': '대중 교통 상세 정보를 보고싶다면, 아래의 카카오맵으로 이동 후 대중교통 경로를 확인하세요',
        
        // 공항 내 안내 섹션
        'airport_heading': '공항 내부 길찾기',
        'airport_description': '공항 내 현재 위치를 설정하고, 주변 시설까지의 거리와 도보 시간을 확인하세요.',
        'get_gps_location': 'GPS로 현재 위치 확인',
        'manual_location_prompt': '또는, 지도에서 가장 가까운 장소를 선택하세요.',
        'map_placeholder': '<i class="fas fa-map-marked-alt" style="font-size: 48px; margin-bottom: 20px; display: block; color: var(--main-teal);"></i><br>위치 확인 후 지도가 표시됩니다',
        'current_location': '현재 위치',
        'current_location_text': '현재 위치',
        'nearby_facilities_heading': '주변 주요 시설',
        'nearby_facilities': '주변 시설',
        'set_location_success': '{type} 위치 설정 완료!',
        'set_location_error': '위치 정보를 가져올 수 없습니다. 수동으로 위치를 설정해주세요.',
        'please_set_location': '위치를 먼저 설정해주세요.',

        // 거리 및 시간 표시
        'distance_m': '{distance}m',
        'distance_km': '{distance}km',
        'walking_time': '• 약 {time}분',
        'already_arrived': '이미 도착함',
        'arrived_to': '{name}로 도착',
        
        // 지도 및 경로 관련
        'view_in_kakaomap': '카카오맵에서 보기',
        'clear_route': '경로 지우기',
        'estimated_route_warning': '예상 경로 • 실제와 다를 수 있음',
        'outside_airport_warning': '인천공항 내에서 사용하세요',
    },
    
    'en': {
        // Header
        'header_title': 'Incheon Airport Navigation',
        'header_subtitle': 'Smart Airport Guide System',
        
        // Tab Menu
        'route_tab_text': 'To the Airport',
        'airport_tab_text': 'In-Airport Guide',
        
        // Route to Airport Section
        'route_heading': 'Optimal Route to Incheon Airport',
        'route_description': 'We will guide you on the distance and time required for vehicles and transportation to Incheon International Airport.',
        'find_route_btn': 'Get Directions from Current Location',
        'route_loading': 'Detecting current location...',
        'route_unsupported': 'Your browser does not support location services.',
        'route_location_success': 'Location confirmed!',
        'route_location_error': 'Could not retrieve location information. Please enable location services.',
        
        // Transportation Information
        'recommended_transport': 'Recommended Transportation',
        'car_to_terminal': 'Car →',
        'taxi_fare': 'Taxi fare: approx',
        'minutes': ' min',
        'currency': ' KRW',
        'real_time_traffic': 'Real-time traffic conditions',
        'airport_bus': 'Incheon International Airport Terminal 1 by public transportation',
        'airport_bus2': 'Incheon International Airport Terminal 2 by public transportation',
        'airport_bus_route': 'Current location → Incheon Airport Terminal 1 Station',
        'airport_bus_route2': 'Current location → Incheon Airport Terminal 2 Station',
        'transit_api_notice': 'If you want to see public transportation details, go to Kakao Maps below and check the public transportation route.',
        
        // In-Airport Guide Section
        'airport_heading': 'In-Airport Navigation',
        'airport_description': 'Set your current location within the airport and check distances and walking times to nearby facilities.',
        'get_gps_location': 'Check Current Location with GPS',
        'manual_location_prompt': 'Or, select the closest location on the map.',
        'map_placeholder': '<i class="fas fa-map-marked-alt" style="font-size: 48px; margin-bottom: 20px; display: block; color: var(--main-teal);"></i><br>Map will be displayed after location confirmation',
        'current_location': 'Current Location',
        'current_location_text': 'Current Location',
        'nearby_facilities_heading': 'Major Facilities Nearby',
        'nearby_facilities': 'Nearby Facilities',
        'set_location_success': '{type} location set!',
        'set_location_error': 'Could not retrieve location information. Please set location manually.',
        'please_set_location': 'Please set your location first.',

        // Distance and Time Display
        'distance_m': '{distance}m',
        'distance_km': '{distance}km',
        'walking_time': '• Approx. {time} mins',
        'already_arrived': 'Already arrived',
        'arrived_to': 'Arrive at {name}',
        
        // Map and Route Related
        'view_in_kakaomap': 'View on Kakao Maps',
        'clear_route': 'Clear Route',
        'estimated_route_warning': 'Expected path • May be different from the real thing',
        'outside_airport_warning': 'Please use within Incheon Airport',
    },
    
    'ja': {
        // ヘッダー
        'header_title': '仁川空港ナビゲーション',
        'header_subtitle': 'スマートな空港案内システム',
        
        // タブメニュー
        'route_tab_text': '空港への道',
        'airport_tab_text': '空港内案内',
        
        // 空港への道セクション
        'route_heading': '仁川空港への最適ルート',
        'route_description': '現在の位置に基づき、仁川空港までの車両および交通の便の距離と所要時間をご案内いたします。',
        'find_route_btn': '現在地から経路を検索',
        'route_loading': '現在地を確認しています...',
        'route_unsupported': '位置情報をサポートしていないブラウザです。',
        'route_location_success': '位置確認完了！',
        'route_location_error': '位置情報を取得できません。位置サービスを有効にしてください。',
        
        // 交通手段情報
        'recommended_transport': 'おすすめの交通手段',
        'car_to_terminal': '車 →',
        'taxi_fare': 'タクシー料金：約',
        'minutes': '分',
        'currency': 'ウォン',
        'real_time_traffic': 'リアルタイム交通状況反映',
        'airport_bus': '公共交通機関で仁川国際空港第1ターミナル',
        'airport_bus2': '公共交通機関で仁川国際空港第2ターミナル',
        'airport_bus_route': '現在地 → 仁川空港1ターミナル駅',
        'airport_bus_route2': '現在の位置 → 仁川空港第2ターミナル駅',
        'transit_api_notice': '公共交通機関の詳細情報をご覧になりたい場合は、下記のカカオマップに移動後、公共交通機関の経路を確認してください.',
        
        // 空港内案内セクション
        'airport_heading': '空港内経路検索',
        'airport_description': '空港内の現在地を設定し、周辺施設までの距離と徒歩時間を確認してください。',
        'get_gps_location': 'GPSで現在地を確認',
        'manual_location_prompt': 'または、地図で最も近い場所を選択してください。',
        'map_placeholder': '<i class="fas fa-map-marked-alt" style="font-size: 48px; margin-bottom: 20px; display: block; color: var(--main-teal);"></i><br>位置確認後、地図が表示されます',
        'current_location': '現在地',
        'current_location_text': '現在地',
        'nearby_facilities_heading': '周辺主要施設',
        'nearby_facilities': '周辺施設',
        'set_location_success': '{type} 位置設定完了！',
        'set_location_error': '位置情報を取得できません。手動で位置を設定してください。',
        'please_set_location': 'まず位置を設定してください。',

        // 距離と時間表示
        'distance_m': '{distance}m',
        'distance_km': '{distance}km',
        'walking_time': '• 約{time}分',
        'already_arrived': '既に到着',
        'arrived_to': '{name}で到着',
        
        // 地図と経路関連
        'view_in_kakaomap': 'カカオマップで見る',
        'clear_route': 'ルートを消去',
        'estimated_route_warning': '予想経路·実際と異なる場合がある',
        'outside_airport_warning': '仁川空港内でご利用ください',
    },
    
    'zh': {
        // 标题
        'header_title': '仁川机场导航',
        'header_subtitle': '智能机场引导系统',
        
        // 选项卡菜单
        'route_tab_text': '前往机场',
        'airport_tab_text': '机场内导航',
        
        // 前往机场部分
        'route_heading': '仁川机场最佳路线',
        'route_description': '以当前位置为基础,介绍到仁川机场的车辆及交通便利距离和所需时间',
        'find_route_btn': '从当前位置查找路线',
        'route_loading': '正在检测当前位置...',
        'route_unsupported': '您的浏览器不支持位置服务。',
        'route_location_success': '位置确认成功！',
        'route_location_error': '无法获取位置信息。请启用位置服务。',
        
        // 交通方式信息
        'recommended_transport': '推荐交通方式',
        'car_to_terminal': '汽车 →',
        'taxi_fare': '出租车费：约',
        'minutes': '分钟',
        'currency': '韩元',
        'real_time_traffic': '实时交通状况反映',
        'airport_bus': '乘坐公共交通到仁川国际机场1号航站楼',
        'airport_bus2': '乘坐公共交通到仁川国际机场2号航站楼',
        'airport_bus_route': '当前位置 → 仁川机场1号航站楼站',
        'airport_bus_route2': '当前位置 → 仁川机场2号航站楼站',
        'transit_api_notice': '如果您想了解公共交通的详细信息，请在移动到下面的kakao map后确认公共交通路线.',
        
        // 机场内导航部分
        'airport_heading': '机场内部导航',
        'airport_description': '设置您在机场内的当前位置，查看附近设施的距离和步行时间。',
        'get_gps_location': '通过GPS确认当前位置',
        'manual_location_prompt': '或者，在地图上选择最近的地点。',
        'map_placeholder': '<i class="fas fa-map-marked-alt" style="font-size: 48px; margin-bottom: 20px; display: block; color: var(--main-teal);"></i><br>确认位置后将显示地图',
        'current_location': '当前位置',
        'current_location_text': '当前位置',
        'nearby_facilities_heading': '周边主要设施',
        'nearby_facilities': '附近设施',
        'set_location_success': '{type} 位置设置成功！',
        'set_location_error': '无法获取位置信息。请手动设置位置。',
        'please_set_location': '请先设置您的位置。',

        // 距离和时间显示
        'distance_m': '{distance}米',
        'distance_km': '{distance}公里',
        'walking_time': '• 约{time}分钟',
        'already_arrived': '已经到达',
        'arrived_to': '到达 {name}',
        
        // 地图和路线相关
        'view_in_kakaomap': '在 Kakao 地图上显示',
        'clear_route': '清除路线',
        'estimated_route_warning': '预期路径 • 可能与实际不符',
        'outside_airport_warning': '请在仁川机场内使用',
    },
    
    'es': {
        // Encabezado
        'header_title': 'Navegación Aeropuerto Incheon',
        'header_subtitle': 'Sistema inteligente de guía aeroportuaria',
        
        // Menú de pestañas
        'route_tab_text': 'Al Aeropuerto',
        'airport_tab_text': 'Guía en el Aeropuerto',
        
        // Sección de ruta al aeropuerto
        'route_heading': 'Ruta Óptima al Aeropuerto de Incheon',
        'route_description': 'Basado en su ubicación actual, le informaremos sobre la distancia y el tiempo que tomará llegar al aeropuerto de Incheon.',
        'find_route_btn': 'Obtener indicaciones desde la ubicación actual',
        'route_loading': 'Detectando ubicación actual...',
        'route_unsupported': 'Su navegador no soporta servicios de ubicación.',
        'route_location_success': '¡Ubicación confirmada!',
        'route_location_error': 'No se pudo recuperar la información de ubicación. Por favor, habilite los servicios de ubicación.',
        
        // Información de transporte
        'recommended_transport': 'Transporte Recomendado',
        'car_to_terminal': 'Coche →',
        'taxi_fare': 'Tarifa de taxi: aprox',
        'minutes': ' min',
        'currency': ' KRW',
        'real_time_traffic': 'Condiciones de tráfico en tiempo real',
        'airport_bus': 'Terminal 1 del Aeropuerto Internacional de Incheon en transporte público',
        'airport_bus2': 'Terminal 2 del Aeropuerto Internacional de Incheon en transporte público',
        'airport_bus_route': 'Ubicación actual → Estación terminal 1 del aeropuerto internacional de Incheon',
        'airport_bus_route2': 'Ubicación actual → Estación terminal 2 del aeropuerto de Incheon',
        'transit_api_notice': 'Si desea ver los detalles del transporte público, vaya al mapa de Kakao a continuación y verifique la ruta del transporte público.',
        
        // Sección de navegación dentro del aeropuerto
        'airport_heading': 'Navegación dentro del Aeropuerto',
        'airport_description': 'Establezca su ubicación actual dentro del aeropuerto y consulte las distancias y tiempos de caminata a las instalaciones cercanas.',
        'get_gps_location': 'Comprobar ubicación actual con GPS',
        'manual_location_prompt': 'O bien, seleccione la ubicación más cercana en el mapa.',
        'map_placeholder': '<i class="fas fa-map-marked-alt" style="font-size: 48px; margin-bottom: 20px; display: block; color: var(--main-teal);"></i><br>El mapa se mostrará después de la confirmación de la ubicación',
        'current_location': 'Ubicación Actual',
        'current_location_text': 'Ubicación Actual',
        'nearby_facilities_heading': 'Principales Instalaciones Cercanas',
        'nearby_facilities': 'Instalaciones Cercanas',
        'set_location_success': '¡Ubicación {type} establecida!',
        'set_location_error': 'No se pudo recuperar la información de ubicación. Por favor, establezca la ubicación manualmente.',
        'please_set_location': 'Por favor, establezca su ubicación primero.',

        // Pantalla de distancia y tiempo
        'distance_m': '{distance}m',
        'distance_km': '{distance}km',
        'walking_time': '• Aprox. {time} minutos',
        'already_arrived': 'Ya llegado',
        'arrived_to': 'Llegada con {name}',
        
        // Mapa y ruta relacionada
        'view_in_kakaomap': 'Vista en el mapa de Kakao',
        'clear_route': 'Limpiar Ruta',
        'estimated_route_warning': 'Camino previsto • Posible diferencia con la realidad',
        'outside_airport_warning': 'Por favor use dentro del Aeropuerto de Incheon',
    }
};