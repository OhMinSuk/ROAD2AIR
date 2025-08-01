// 네비게이션 경로 추가(공항 가는 길)
const airportTerminals = {
    terminal1: {
        name: {
            ko: '인천국제공항 제1터미널역',
            en: 'Incheon International Airport Terminal 1 Station',
            ja: '仁川国際空港第1ターミナル駅',
            zh: '仁川国际机场第1航站楼站',
            es: 'Estación terminal 1 del Aeropuerto Internacional de Incheon'
        },
        lat: 37.447660711,
        lng: 126.452329312,
        code: 'ICN_T1',
        stationName: {
            ko: '인천공항1터미널역',
            en: 'Incheon Int\'l Airport Terminal 1 Station',
            ja: '仁川空港第1ターミナル駅',
            zh: '仁川机场第1航站楼站',
            es: 'Estación Terminal 1 del Aeropuerto de Incheon'
        }
    },
    terminal2: {
        name: {
            ko: '인천국제공항 제2터미널역',
            en: 'Incheon International Airport Terminal 2 Station',
            ja: '仁川国際空港第2ターミナル駅',
            zh: '仁川国际机场第2航站楼站',
            es: 'Estación terminal 2 del Aeropuerto Internacional de Incheon'
        },
        lat: 37.468741034,
        lng: 126.433512468,
        code: 'ICN_T2',
        stationName: {
            ko: '인천공항2터미널역',
            en: 'Incheon Int\'l Airport Terminal 2 Station',
            ja: '仁川空港第2ターミナル駅',
            zh: '仁川机场第2航站楼站',
            es: 'Estación Terminal 2 del Aeropuerto de Incheon'
        }
    }
};

// 시설 정보 여기 추가!!!!
const airportFacilities = [
    { 
        name: {
            ko: "제1터미널 출국장 (3층)",
            en: "Terminal 1 Departure (3F)",
            ja: "第1ターミナル出発ロビー (3階)",
            zh: "第1航站楼出发大厅 (3层)",
            es: "Terminal 1 Salidas (3º piso)"
        },
        lat: 37.44989134944285, 
        lng: 126.45181830881407, 
        description: {
            ko: "국내선 및 국제선 출발 체크인",
            en: "Domestic and International Departure Check-in",
            ja: "国内線・国際線出発チェックイン",
            zh: "国内和国际航班出发值机",
            es: "Check-in de Salidas Nacionales e Internacionales"
        }
    },
    { 
        name: {
            ko: "제2터미널 출국장 (3층)",
            en: "Terminal 2 Departure (3F)",
            ja: "第2ターミナル出発ロビー (3階)",
            zh: "第2航站楼出发大厅 (3层)",
            es: "Terminal 2 Salidas (3º piso)"
        },
        lat: 37.467062102673665, 
        lng: 126.43347812383803, 
        description: {
            ko: "국제선 출발 체크인",
            en: "International Departure Check-in",
            ja: "国際線出発チェックイン",
            zh: "国际航班出发值机",
            es: "Check-in de Salidas Internacionales"
        }
    },
    {
        name: {
            ko: "화장실",
            en: "Restroom",
            ja: "トイレ",
            zh: "洗手间",
            es: "Baño"
        },
        lat: 37.45006357192358,
        lng: 126.45247206550808,
        description: {
            ko: "제1여객터미널 3층 동편 3번출국장 우측",
            en: "Right side of Departure Gate 3, East Wing, 3F, Terminal 1",
            ja: "第1旅客ターミナル3階 東側 出国ゲート3の右側",
            zh: "第1航站楼3层东侧3号出境口右侧",
            es: "A la derecha de la puerta de salida 3, ala este, 3er piso, Terminal 1"
        }
    },
    {
        name: {
            ko: "출국장 2",
            en: "Departure Gate 2",
            ja: "出国ゲート2",
            zh: "出境口2",
            es: "Puerta de salida 2"
        },
        lat: 37.45015237482217,
        lng: 126.45299448040555,
        description: {
            ko: "제 1 여객터미널",
            en: "Terminal 1",
            ja: "第1旅客ターミナル",
            zh: "第1航站楼",
            es: "Terminal 1"
        }
    },
    {
        name: {
            ko: "출국장 5",
            en: "Departure Gate 5",
            ja: "出国ゲート5",
            zh: "出境口5",
            es: "Puerta de salida 5"
        },
        lat: 37.44794487639882,
        lng: 126.44908168708227,
        description: {
            ko: "제 1 여객터미널",
            en: "Terminal 1",
            ja: "第1旅客ターミナル",
            zh: "第1航站楼",
            es: "Terminal 1"
        }
    },
        {
        name: {
            ko: "[현대면세점] 프라다",
            en: "[Hyundai Duty Free] Prada",
            ja: "[ヒュンダイ免税店] プラダ",
            zh: "[现代免税店] 普拉达",
            es: "[Hyundai Duty Free] Prada"
        },
        lat: 37.449972360415146,
        lng: 126.45074873453193,
        description: {
            ko: "제1여객터미널 3층 27번 게이트 부근",
            en: "Near Gate 27, 3F, Terminal 1",
            ja: "第1旅客ターミナル 3階 27番ゲート付近",
            zh: "第1航站楼3层27号登机口附近",
            es: "Cerca de la puerta 27, 3er piso, Terminal 1"
        }
    },
    {
        name: {
            ko: "[현대면세점] 샤넬",
            en: "[Hyundai Duty Free] Chanel",
            ja: "[ヒュンダイ免税店] シャネル",
            zh: "[现代免税店] 香奈儿",
            es: "[Hyundai Duty Free] Chanel"
        },
        lat: 37.4495185430674,
        lng: 126.4499544451474,
        description: {
            ko: "제1여객터미널 3층 28번 게이트 부근",
            en: "Near Gate 28, 3F, Terminal 1",
            ja: "第1旅客ターミナル 3階 28番ゲート付近",
            zh: "第1航站楼3层28号登机口附近",
            es: "Cerca de la puerta 28, 3er piso, Terminal 1"
        }
    },
    {
        name: {
            ko: "[신세계면세점] 주류/담배/식품",
            en: "[Shinsegae Duty Free] Liquor/Tobacco/Food",
            ja: "[新世界免税店] 酒・たばこ・食品",
            zh: "[新世界免税店] 酒类/香烟/食品",
            es: "[Shinsegae Duty Free] Licores/Tabaco/Alimentos"
        },
        lat: 37.45032300707973,
        lng: 126.4522752250475,
        description: {
            ko: "제1여객터미널 3층 면세지역 25번 탑승구 부근",
            en: "Near Gate 25, Duty-Free Area, 3F, Terminal 1",
            ja: "第1旅客ターミナル 3階 免税エリア 25番ゲート付近",
            zh: "第1航站楼3层免税区25号登机口附近",
            es: "Cerca de la puerta 25, zona duty-free, 3er piso, Terminal 1"
        }
    },
    {
        name: {
            ko: "쉐이크쉑",
            en: "Shake Shack",
            ja: "シェイクシャック",
            zh: "Shake Shack（奶昔汉堡）",
            es: "Shake Shack"
        },
        lat: 37.44912616430473,
        lng: 126.45022560819406,
        description: {
            ko: "제1여객터미널 3층 일반지역 H 체크인카운터 부근",
            en: "Near Check-in Counter H, Public Area, 3F, Terminal 1",
            ja: "第1旅客ターミナル3階 一般エリア Hチェックインカウンター付近",
            zh: "第1航站楼3层公共区域H值机柜台附近",
            es: "Cerca del mostrador de facturación H, zona pública, 3er piso, Terminal 1"
        }
    }
];
