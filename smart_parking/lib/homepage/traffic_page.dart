// Written by Tim Hudson - Last Updated 4/1/2025
// Written with the assistance of Openstack, Google Codelabs and ChatGPT

// This code is responsible for the traffic page that displays a value of how heavy the traffic is from a scale of low, medium and heavy
// It does this by taking the saved home address and the saved garage address from the database, and when the button is clicked, runs the script and siplays the result on the same page.

// Import the needed packages
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter/gestures.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import 'special_events_loader.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:google_fonts/google_fonts.dart';
import '../widgets/appbar_datetime_center.dart';
import '../config/api_config.dart';

class TrafficPage extends StatefulWidget {
  const TrafficPage({super.key});

  @override
  _TrafficPageState createState() => _TrafficPageState();
}

class _TrafficPageState extends State<TrafficPage> {
  static const String _tomtomApiKey =
      String.fromEnvironment('TOMTOM_API_KEY', defaultValue: '');
  static const String _backendBaseUrl = ApiConfig.backendBaseUrl;

  final ScrollController _forecastScrollController = ScrollController();
  double _forecastScrollValue = 0;
  String _weatherInfo = "Fetching weather...";
  String _weatherAlert = "No alerts";
  bool _weatherLoading = false;
  List<Map<String, dynamic>> _forecast = [];
  bool _forecastLoading = false;

  Future<void> _fetchWeatherAndForecast() async {
    setState(() {
      _weatherLoading = true;
      _forecastLoading = true;
      _weatherInfo = "Fetching weather...";
      _weatherAlert = "No alerts";
      _forecast = [];
    });
    String weather = await getWeatherStatus();
    String alert = _checkWeatherAlert(weather);
    List<Map<String, dynamic>> forecast = await getWeatherForecast();
    setState(() {
      _weatherInfo = weather;
      _weatherAlert = alert;
      _weatherLoading = false;
      _forecast = forecast;
      _forecastLoading = false;
    });
  }

  Future<void> _fetchWeather() async {
    setState(() {
      _weatherLoading = true;
      _weatherInfo = "Fetching weather...";
      _weatherAlert = "No alerts";
    });
    String weather = await getWeatherStatus();
    String alert = _checkWeatherAlert(weather);
    setState(() {
      _weatherInfo = weather;
      _weatherAlert = alert;
      _weatherLoading = false;
    });
  }

  Future<List<Map<String, dynamic>>> getWeatherForecast() async {
    try {
      final url = Uri.parse('$_backendBaseUrl/weather/forecast');
      final response = await http.get(url);
      if (response.statusCode != 200) {
        return [];
      }
      final data = json.decode(response.body);
      final List<dynamic> list = data['forecast'] ?? [];
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      List<Map<String, dynamic>> forecasts = [];
      for (var entry in list) {
        final dt = DateTime.fromMillisecondsSinceEpoch(
                (entry['dt'] ?? 0) * 1000,
                isUtc: true)
            .toLocal();
        if (dt.day == today.day) {
          final temp = entry['main']?['temp'];
          final desc = entry['weather']?[0]?['description'] ?? '';
          if (temp != null || (desc is String && desc.isNotEmpty)) {
            forecasts.add({
              'time': DateTime(today.year, today.month, today.day, dt.hour),
              'temp': temp,
              'desc': desc,
            });
          }
        }
      }
      return forecasts;
    } catch (e) {
      return [];
    }
  }

  Future<String> getWeatherStatus() async {
    try {
      final url = Uri.parse('$_backendBaseUrl/weather/current');
      final response = await http.get(url);
      if (response.statusCode != 200) {
        return "Failed to retrieve weather data (${response.statusCode})";
      }
      final data = json.decode(response.body);
      if (data['summary'] != null && data['summary'].toString().isNotEmpty) {
        return data['summary'].toString();
      }
      return 'Weather data unavailable';
    } catch (e) {
      return "Error: $e";
    }
  }

  String _checkWeatherAlert(String weather) {
    if (weather.contains("snow") || weather.contains("Snow")) {
      return "⚠️ Snowy conditions!";
    } else if (weather.contains("rain") || weather.contains("Rain")) {
      return "⚠️ Rainy weather!";
    } else if (weather.contains("hot") || weather.contains("35°C")) {
      return "🔥 Extreme heat!";
    }
    return "No alerts";
  }

  Future<void> _fetchTrafficAndIncidents() async {
    setState(() {
      _trafficLoading = true;
      _incidentsLoading = true;
      _trafficInfo = "Fetching traffic...";
      _trafficAlert = "No alerts";
      _trafficIncidents = [];
    });
    String traffic = await getTrafficStatus();
    String alert = _checkTrafficAlert(traffic);
    List<Map<String, dynamic>> incidents = await getTrafficIncidents();
    setState(() {
      _trafficInfo = traffic;
      _trafficAlert = alert;
      _trafficLoading = false;
      _trafficIncidents = incidents;
      _incidentsLoading = false;
    });
  }

  Future<void> _fetchTraffic() async {
    setState(() {
      _trafficLoading = true;
      _trafficInfo = "Fetching traffic...";
      _trafficAlert = "No alerts";
    });
    String traffic = await getTrafficStatus();
    String alert = _checkTrafficAlert(traffic);
    setState(() {
      _trafficInfo = traffic;
      _trafficAlert = alert;
      _trafficLoading = false;
    });
  }

  Future<List<Map<String, dynamic>>> getTrafficIncidents() async {
    try {
      // TomTom Traffic Incidents API for Harrisonburg area
      if (_tomtomApiKey.isEmpty) {
        return [];
      }
      const double lat = 38.4495;
      const double lon = -78.8690;
      const double radius = 10000; // 10km radius around JMU

      final url = Uri.parse(
        'https://api.tomtom.com/traffic/services/5/incidentDetails?key=$_tomtomApiKey&bbox=${lon - 0.1},${lat - 0.1},${lon + 0.1},${lat + 0.1}&fields=incidents{type,geometry,properties{iconCategory,magnitudeOfDelay,events{description,code},startTime,endTime}}&language=en&categoryFilter=0,1,2,3,4,5,6,7,8,9,10,11,14',
      );

      final response = await http.get(url);
      if (response.statusCode != 200) {
        return [];
      }

      final data = json.decode(response.body);
      final List<dynamic> incidents = data['incidents'] ?? [];
      List<Map<String, dynamic>> processedIncidents = [];

      for (var incident in incidents.take(5)) {
        // Limit to 5 incidents
        final properties = incident['properties'] ?? {};
        final events = properties['events'] ?? [];
        String description = 'Traffic incident';
        if (events.isNotEmpty && events[0]['description'] != null) {
          description = events[0]['description'];
        }

        processedIncidents.add({
          'description': description,
          'delay': properties['magnitudeOfDelay'] ?? 0,
          'category': properties['iconCategory'] ?? 0,
        });
      }
      return processedIncidents;
    } catch (e) {
      return [];
    }
  }

  Future<String> getTrafficStatus() async {
    try {
      // TomTom Traffic Flow API for general area traffic
      if (_tomtomApiKey.isEmpty) {
        return "Failed to retrieve traffic data (TOMTOM_API_KEY not configured)";
      }
      const double lat = 38.4495;
      const double lon = -78.8690;

      final url = Uri.parse(
        'https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point=$lat,$lon&unit=mph&key=$_tomtomApiKey',
      );

      final response = await http.get(url);
      if (response.statusCode != 200) {
        return "Failed to retrieve traffic data (${response.statusCode})";
      }

      final data = json.decode(response.body);
      final flowSegmentData = data['flowSegmentData'];

      if (flowSegmentData != null) {
        final currentSpeed = flowSegmentData['currentSpeed'] ?? 0;
        final freeFlowSpeed = flowSegmentData['freeFlowSpeed'] ?? currentSpeed;
        final confidence = flowSegmentData['confidence'] ?? 0.5;

        String trafficLevel = _calculateTrafficLevel(
            currentSpeed.toDouble(), freeFlowSpeed.toDouble());
        String confidenceText =
            confidence > 0.7 ? "High confidence" : "Moderate confidence";

        return '$trafficLevel traffic conditions in Harrisonburg area. Current speed: ${currentSpeed}mph ($confidenceText)';
      } else {
        return "Traffic conditions: Normal flow expected in Harrisonburg area";
      }
    } catch (e) {
      return "Error: $e";
    }
  }

  String _calculateTrafficLevel(double currentSpeed, double freeFlowSpeed) {
    if (freeFlowSpeed == 0) return "Normal";

    double ratio = currentSpeed / freeFlowSpeed;
    if (ratio >= 0.8) {
      return "Light";
    } else if (ratio >= 0.5) {
      return "Moderate";
    } else {
      return "Heavy";
    }
  }

  String _checkTrafficAlert(String traffic) {
    if (traffic.contains("Heavy")) {
      return "🚗 Heavy traffic conditions!";
    } else if (traffic.contains("Moderate")) {
      return "⚠️ Moderate traffic delays";
    } else if (traffic.contains("Error") || traffic.contains("Failed")) {
      return "❌ Traffic data unavailable";
    }
    return "No alerts";
  }

  Future<void> _fetchEvents() async {
    setState(() {
      _eventsLoading = true;
      _eventsInfo = "Fetching events...";
      _todaysEvents = [];
    });

    List<Map<String, dynamic>> events = await loadSpecialEventsForToday();
    String eventsInfo = events.isEmpty
        ? "No campus events today"
        : "${events.length} campus event(s) today";

    setState(() {
      _eventsInfo = eventsInfo;
      _todaysEvents = events;
      _eventsLoading = false;
    });
  }

  List<Map<String, dynamic>> _getMockEvents() {
    // Mock events for testing - remove when you have real API key
    final now = DateTime.now();
    switch (now.weekday) {
      case 1: // Monday
        return [
          {
            'title': 'Student Government Meeting',
            'time': '6:00 PM',
            'location': 'Taylor Hall'
          }
        ];
      case 2: // Tuesday
        return [
          {
            'title': 'Career Fair',
            'time': '10:00 AM - 4:00 PM',
            'location': 'Festival Conference Center'
          }
        ];
      case 3: // Wednesday
        return [
          {
            'title': 'Guest Lecture: Technology Innovation',
            'time': '2:00 PM',
            'location': 'ISAT Building'
          }
        ];
      case 4: // Thursday
        return [
          {
            'title': 'Basketball Game vs. ODU',
            'time': '7:00 PM',
            'location': 'Convocation Center'
          }
        ];
      case 5: // Friday
        return [
          {
            'title': 'Campus Movie Night',
            'time': '8:00 PM',
            'location': 'Grafton-Stovall Theatre'
          }
        ];
      case 6: // Saturday
        return [
          {
            'title': 'Farmers Market',
            'time': '9:00 AM - 1:00 PM',
            'location': 'Festival Lawn'
          }
        ];
      case 7: // Sunday
        return [
          {
            'title': 'Study Group Session',
            'time': '7:00 PM',
            'location': 'Carrier Library'
          }
        ];
      default:
        return [];
    }
  }

  // Traffic-related variables
  String _trafficInfo = "Fetching traffic...";
  String _trafficAlert = "No alerts";
  bool _trafficLoading = false;
  List<Map<String, dynamic>> _trafficIncidents = [];
  bool _incidentsLoading = false;

  // Events-related variables
  String _eventsInfo = "Fetching events...";
  bool _eventsLoading = false;
  List<Map<String, dynamic>> _todaysEvents = [];

  // Placeholder for legacy variables
  String _trafficStatus = 'Traffic status will be displayed here...';
  String _homeAddress = 'Login to select these addresses';
  String _favoriteGarage = 'Login to select these addresses';
  late Timer _timer;

  // Google Map state
  late GoogleMapController mapController;
  final LatLng _center = const LatLng(38.4392, -78.8749); // JMU campus
  // OG marker types and state
  BitmapDescriptor lotIcon =
      BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue);
  BitmapDescriptor garageIcon =
      BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueYellow);
  Set<Marker> residentLot = {
    Marker(
        markerId: const MarkerId("R1 Lot"),
        position: const LatLng(38.43730, -78.86554),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R1 Lot", snippet: "A Parking lot near the Village")),
    Marker(
        markerId: const MarkerId("R2 Lot"),
        position: const LatLng(38.43003, -78.87736),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow:
            const InfoWindow(title: "R2 Lot", snippet: "A Parking lot near Xlabs")),
    Marker(
        markerId: const MarkerId("R3 Lot"),
        position: const LatLng(38.43863, -78.87984),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R3 Lot", snippet: "A Parking lot near the Quad")),
    Marker(
        markerId: const MarkerId("R6 Lot"),
        position: const LatLng(38.43009, -78.86627),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R6 Lot", snippet: "A Parking lot near the Paul Jennings")),
    Marker(
        markerId: const MarkerId("R8 Lot"),
        position: const LatLng(38.43862, -78.86392),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R8 Lot", snippet: "A Parking lot near the Village")),
    Marker(
        markerId: const MarkerId("R9 Lot"),
        position: const LatLng(38.44648, -78.87849),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R9 Lot", snippet: "A Parking lot near the Memorial Hall")),
    Marker(
        markerId: const MarkerId("R10 Lot"),
        position: const LatLng(38.42681, -78.87594),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R10 Lot",
            snippet: "A Parking lot near University Outpost")),
    Marker(
        markerId: const MarkerId("R13 Lot"),
        position: const LatLng(38.44423, -78.87717),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R13 Lot",
            snippet: "A Parking lot located near Memorial Hall")),
    Marker(
        markerId: const MarkerId("R14 Lot"),
        position: const LatLng(38.44371, -78.87641),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R14 Lot",
            snippet: "A Parking lot located near Grace Street Apts")),
    Marker(
        markerId: const MarkerId("R15 Lot"),
        position: const LatLng(38.44311, -78.87666),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R15 Lot",
            snippet: "A Parking lot located near Grace Street Apts")),
    Marker(
        markerId: const MarkerId("R16 Lot"),
        position: const LatLng(38.44337, -78.87721),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R16 Lot",
            snippet: "A Parking lot located near Grace Street Apts")),
    Marker(
        markerId: const MarkerId("R17 Lot"),
        position: const LatLng(38.43743, -78.87955),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R17 Lot", snippet: "A Small Parking lot near the Quad")),
    Marker(
        markerId: const MarkerId("R18 Lot"),
        position: const LatLng(38.43709, -78.87948),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R18 Lot", snippet: "A Small Parking lot near the Quad")),
    Marker(
        markerId: const MarkerId("R19 Lot"),
        position: const LatLng(38.43657, -78.87878),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R19 Lot", snippet: "A Small Parking lot near the Quad")),
    Marker(
        markerId: const MarkerId("R20 Lot"),
        position: const LatLng(38.43594, -78.87931),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "R20 Lot", snippet: "A Small Parking lot near the Quad")),
  };
  Set<Marker> commuterLot = {
    Marker(
        markerId: const MarkerId("C3 Lot"),
        position: const LatLng(38.43619, -78.86565),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "C3 Lot",
            snippet: "A Small Parking lot near the Longfield ")),
    Marker(
        markerId: const MarkerId("C4 Lot"),
        position: const LatLng(38.43816, -78.86598),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "C4 Lot", snippet: "A Parking lot near the Village")),
    Marker(
        markerId: const MarkerId("C5 Lot"),
        position: const LatLng(38.43380, -78.87110),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "C5 Lot",
            snippet: "A Parking lot near the College of Business")),
    Marker(
        markerId: const MarkerId("C8 Lot"),
        position: const LatLng(38.44574, -78.87798),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "C8 Lot", snippet: "A Parking lot near the Memorial Hall")),
    Marker(
        markerId: const MarkerId("C9 Lot"),
        position: const LatLng(38.43432, -78.86999),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "C9 Lot", snippet: "A Parking lot near Duke Dog Alley")),
    Marker(
        markerId: const MarkerId("C13 Lot"),
        position: const LatLng(38.44730, -78.87852),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
        infoWindow: const InfoWindow(
            title: "C13 Lot",
            snippet: "A Parking lot near Memorial Art Complex")),
  };
  Set<Marker> markerGarage = {
    Marker(
        markerId: const MarkerId("Warsaw Deck"),
        position: const LatLng(38.44065, -78.87756),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueYellow),
        infoWindow: const InfoWindow(
            title: "Warsaw Deck",
            snippet: "A Parking Deck located near Forbes and the Quad")),
    Marker(
        markerId: const MarkerId("Chesapeake Deck"),
        position: const LatLng(38.44273, -78.87711),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueYellow),
        infoWindow: const InfoWindow(
            title: "Chesapeake Deck",
            snippet:
                "A Parking Deck located near Forbes and Grace Street Apts")),
    Marker(
        markerId: const MarkerId("Grace Deck"),
        position: const LatLng(38.44121, -78.87790),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueYellow),
        infoWindow: const InfoWindow(
            title: "Grace Deck",
            snippet: "A Parking Deck located near the Student Success Center")),
    Marker(
        markerId: const MarkerId("Ballard Deck"),
        position: const LatLng(38.43102, -78.85838),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueYellow),
        infoWindow: const InfoWindow(
            title: "Ballard Deck",
            snippet: "A Parking Deck located near Festival and the AUBC")),
    Marker(
        markerId: const MarkerId("Champions Deck"),
        position: const LatLng(38.43487, -78.87400),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueYellow),
        infoWindow: const InfoWindow(
            title: "Champions Deck",
            snippet: "A Parking Deck located near Bridgeforth Stadium")),
    Marker(
        markerId: const MarkerId("Mason Deck"),
        position: const LatLng(38.44131, -78.87197),
        icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueYellow),
        infoWindow: const InfoWindow(
            title: "Mason Deck",
            snippet: "A Parking Deck located near Student Success Center")),
  };
  List<String> markerTypes = ['All', 'Resident', 'Commuter', 'Garage'];
  String selectedType = 'All';
  Set<Marker> _markers = {};
  void filterMarkers(String setting) {
    Set<Marker> result = {};
    switch (setting) {
      case 'Resident':
        result = residentLot;
        break;
      case "Commuter":
        result = commuterLot;
        break;
      case 'Garage':
        result = markerGarage;
        break;
      case 'All':
        result = residentLot.union(markerGarage).union(commuterLot);
    }
    setState(() {
      _markers = result;
    });
  }

  void _onMapCreated(GoogleMapController controller) {
    mapController = controller;
  }

  Future<void> _getUserData() async {
    final User? user = FirebaseAuth.instance.currentUser;

    if (user != null) {
      try {
        DocumentSnapshot userDoc = await FirebaseFirestore.instance
            .collection('users')
            .doc(user.uid)
            .get();
        if (userDoc.exists) {
          setState(() {
            _homeAddress =
                userDoc['homeAddress'] ?? 'Login to select these addresses';
            _favoriteGarage = userDoc['favoriteGarage']['address'] ??
                'Login to select these addresses';
          });
        }
      } catch (e) {
        setState(() {
          _trafficStatus = "Error fetching user data: $e";
        });
      }
    } else {
      setState(() {
        _homeAddress = 'Login to set this addresses';
        _favoriteGarage = 'Login to set this addresses';
        _trafficStatus = 'Traffic status will be displayed here';
      });
    }
  }

  Future<void> _getTrafficStatus() async {
    // Replace old Google Directions logic with TomTom traffic data
    await _fetchTrafficAndIncidents();
  }

  void _startUserDataTimer() {
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      _getUserData();
    });
  }

  void _syncForecastSlider() {
    if (!_forecastScrollController.hasClients) {
      return;
    }
    final max = _forecastScrollController.position.maxScrollExtent;
    final nextValue = max > 0
        ? (_forecastScrollController.offset / max).clamp(0.0, 1.0)
        : 0.0;

    if ((_forecastScrollValue - nextValue).abs() > 0.001 && mounted) {
      setState(() {
        _forecastScrollValue = nextValue;
      });
    }
  }

  void _onForecastSliderChanged(double value) {
    if (!_forecastScrollController.hasClients) {
      return;
    }
    final max = _forecastScrollController.position.maxScrollExtent;
    final targetOffset = max * value;
    _forecastScrollController.jumpTo(targetOffset);
    setState(() {
      _forecastScrollValue = value;
    });
  }

  void _onForecastPointerSignal(PointerSignalEvent event) {
    if (event is! PointerScrollEvent || !_forecastScrollController.hasClients) {
      return;
    }

    final double delta =
        event.scrollDelta.dy != 0 ? event.scrollDelta.dy : event.scrollDelta.dx;
    final double max = _forecastScrollController.position.maxScrollExtent;
    final double target =
        (_forecastScrollController.offset + delta).clamp(0.0, max);
    _forecastScrollController.jumpTo(target);
  }

  @override
  void initState() {
    super.initState();
    _forecastScrollController.addListener(_syncForecastSlider);
    _getUserData();
    _startUserDataTimer();
    _markers = residentLot.union(markerGarage).union(commuterLot);
    _fetchWeatherAndForecast();
    _fetchTrafficAndIncidents();
    _fetchEvents();
  }

  @override
  void dispose() {
    _timer.cancel();
    _forecastScrollController.removeListener(_syncForecastSlider);
    _forecastScrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final double topPanelInset = mediaQuery.padding.top + kToolbarHeight + 12;
    final double bottomPanelInset = mediaQuery.padding.bottom + 12;
    final double viewportPanelHeight =
      mediaQuery.size.height - topPanelInset - bottomPanelInset;
    final double stackedPanelHeight =
      (viewportPanelHeight * 1.8).clamp(980.0, 1320.0).toDouble();
    const double panelVerticalOffset = 0;
    final double pageHorizontalPadding =
        (mediaQuery.size.width * 0.028).clamp(14.0, 34.0).toDouble();
    final double pageVerticalPadding =
        (mediaQuery.size.height * 0.018).clamp(10.0, 22.0).toDouble();
    final double sectionGap =
      (mediaQuery.size.width * 0.012).clamp(10.0, 18.0).toDouble();
    final double cardPadding =
      (mediaQuery.size.width * 0.014).clamp(14.0, 20.0).toDouble();
    final double itemPadding =
        (mediaQuery.size.width * 0.011).clamp(10.0, 16.0).toDouble();
    final double itemSpacing =
        (mediaQuery.size.width * 0.007).clamp(6.0, 12.0).toDouble();
    final double chipSide =
      (mediaQuery.size.width * 0.088).clamp(96.0, 124.0).toDouble();
    final double contentScale =
      (mediaQuery.size.width / 1200).clamp(0.96, 1.18).toDouble();
    final double rightPanelScale =
      (contentScale * 0.96).clamp(0.90, 1.05).toDouble();
    final double rightPanelIconSize =
        (22 * rightPanelScale).clamp(18.0, 24.0).toDouble();
    final bool stackCards = mediaQuery.size.width < 980;
    final bool compactWeatherLayout =
      mediaQuery.size.width < 430 || mediaQuery.size.height < 760;
    final double containerWidth =
      (mediaQuery.size.width * 0.80).clamp(320.0, 1100.0).toDouble();
    const double cardsGap = 4.0; // match map/filter gap
    const Color neutralCardBorder = Color.fromRGBO(220, 220, 226, 1);

    return Scaffold(
      backgroundColor: const Color.fromRGBO(0, 0, 0, 1),
      extendBody: true,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        centerTitle: false,
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Today',
              style: GoogleFonts.montserrat(fontWeight: FontWeight.w500),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: const Icon(Icons.help_outline),
              tooltip: 'Instructions',
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Instructions'),
                    content: const Text('This dashboard provides real-time updates on campus events, traffic, and weather. Use the refresh buttons to update each section.'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text('Close'),
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ),
        backgroundColor: Colors.transparent,
        foregroundColor: const Color.fromRGBO(255, 255, 255, 1),
        elevation: 0,
        scrolledUnderElevation: 0,
        shadowColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        flexibleSpace: const AppBarDateTimeCenter(),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign Out',
            onPressed: () async {
              await FirebaseAuth.instance.signOut();
              Navigator.pop(context);
            },
          ),
        ],
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.bottomLeft,
            end: Alignment.topRight,
            colors: [
              Color.fromRGBO(0, 0, 0, 1),
              Color.fromRGBO(69, 0, 132, 1),
            ],
          ),
        ),
        child: Stack(
          children: [
            Positioned.fill(
              child: Padding(
                padding: EdgeInsets.only(
                  top: topPanelInset,
                  left: pageHorizontalPadding,
                  right: pageHorizontalPadding,
                  bottom: bottomPanelInset,
                ),
                child: SingleChildScrollView(
                  physics: stackCards
                      ? const AlwaysScrollableScrollPhysics()
                      : const NeverScrollableScrollPhysics(),
                  child: Center(
                    child: SizedBox(
                      width: containerWidth,
                      height: stackCards ? stackedPanelHeight : viewportPanelHeight,
                      child: Transform.translate(
                      offset: const Offset(panelVerticalOffset, panelVerticalOffset),
                      child: MediaQuery(
                        data: mediaQuery.copyWith(
                          textScaler: TextScaler.linear(contentScale),
                        ),
                        child: IconTheme(
                          data: IconThemeData(
                            size: (24 * contentScale).clamp(20.0, 30.0).toDouble(),
                          ),
                          child: Flex(
                              direction: stackCards ? Axis.vertical : Axis.horizontal,
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Expanded(
                                  flex: stackCards ? 3 : 6,
                                  child: Card(
                                      margin: EdgeInsets.zero,
                                      elevation: 1.5,
                                      clipBehavior: Clip.antiAlias,
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(16),
                                        side: const BorderSide(color: neutralCardBorder),
                                      ),
                                      color: const Color.fromRGBO(247, 247, 249, 1),
                                      child: Padding(
                                        padding: EdgeInsets.all(cardPadding),
                                        child: Column(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          mainAxisSize: MainAxisSize.max,
                                          children: [
                                            Row(
                                              children: [
                                                const Icon(Icons.event, color: Color.fromRGBO(158, 158, 158, 1)),
                                                const SizedBox(width: 8),
                                                Text('Campus Events', style: Theme.of(context).textTheme.titleMedium),
                                                const Spacer(),
                                                _eventsLoading
                                                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                                                    : IconButton(
                                                        icon: const Icon(Icons.refresh),
                                                        tooltip: 'Refresh',
                                                        onPressed: _fetchEvents,
                                                      ),
                                              ],
                                            ),
                                            SizedBox(height: sectionGap * 0.35),
                                            Divider(height: 1, thickness: 1, color: Colors.grey.shade400),
                                            SizedBox(height: sectionGap * 1.15),
                                            if (_todaysEvents.isNotEmpty)
                                              Padding(
                                                padding: EdgeInsets.only(bottom: sectionGap * 0.2),
                                                child: Text(_eventsInfo, style: const TextStyle(fontSize: 17)),
                                              ),
                                            SizedBox(height: sectionGap * 0.25),
                                            Text('Today\'s Events:', style: Theme.of(context).textTheme.titleSmall),
                                            const SizedBox(height: 4),
                                            Expanded(
                                              child: _todaysEvents.isNotEmpty
                                                  ? ScrollConfiguration(
                                                      behavior: ScrollConfiguration.of(context).copyWith(scrollbars: true),
                                                      child: ListView.builder(
                                                        physics: const AlwaysScrollableScrollPhysics(),
                                                        itemCount: _todaysEvents.length,
                                                        itemBuilder: (context, index) {
                                                          final event = _todaysEvents[index];
                                                          return Container(
                                                            width: double.infinity,
                                                            margin: EdgeInsets.only(bottom: itemSpacing),
                                                            padding: EdgeInsets.all(itemPadding),
                                                            decoration: BoxDecoration(
                                                              color: Colors.white,
                                                              borderRadius: BorderRadius.circular(8),
                                                            ),
                                                            child: Column(
                                                              crossAxisAlignment: CrossAxisAlignment.start,
                                                              children: [
                                                                Text(
                                                                  event['title'] ?? 'Campus Event',
                                                                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                                                                  maxLines: 2,
                                                                  overflow: TextOverflow.ellipsis,
                                                                ),
                                                                SizedBox(height: itemSpacing * 0.5),
                                                                Text('⏰ ${event['time'] ?? 'TBD'}', style: const TextStyle(fontSize: 14, color: Colors.blue)),
                                                                if (event['location'] != null)
                                                                  Text('📍 ${event['location']}', style: const TextStyle(fontSize: 14, color: Colors.green)),
                                                              ],
                                                            ),
                                                          );
                                                        },
                                                      ),
                                                    )
                                                  : Container(
                                                      width: double.infinity,
                                                      padding: const EdgeInsets.all(12),
                                                      decoration: BoxDecoration(
                                                        color: Colors.grey.shade100,
                                                        borderRadius: BorderRadius.circular(8),
                                                      ),
                                                      child: const Center(
                                                        child: Text(
                                                          '📅 No events scheduled for today',
                                                          style: TextStyle(fontSize: 14, color: Colors.grey),
                                                          textAlign: TextAlign.center,
                                                        ),
                                                      ),
                                                    ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                ),
                                SizedBox(
                                  width: stackCards ? 0 : cardsGap,
                                  height: stackCards ? cardsGap : 0,
                                ),
                                Expanded(
                                  flex: stackCards ? 5 : 4,
                                  child: MediaQuery(
                                    data: mediaQuery.copyWith(
                                      textScaler: TextScaler.linear(rightPanelScale),
                                    ),
                                    child: IconTheme(
                                      data: IconThemeData(size: rightPanelIconSize),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.stretch,
                                        children: [
                                          Expanded(
                                            flex: stackCards ? 1 : 1,
                                            child: Card(
                                              margin: EdgeInsets.zero,
                                              elevation: 1.5,
                                              clipBehavior: Clip.antiAlias,
                                              shape: RoundedRectangleBorder(
                                                borderRadius: BorderRadius.circular(16),
                                                side: const BorderSide(color: neutralCardBorder),
                                              ),
                                              color: const Color.fromRGBO(247, 247, 249, 1),
                                              child: Padding(
                                                padding: EdgeInsets.all(cardPadding),
                                                child: Column(
                                                  crossAxisAlignment: CrossAxisAlignment.stretch,
                                                  children: [
                                                    Padding(
                                                      padding: EdgeInsets.only(bottom: sectionGap * 0.25),
                                                      child: Row(
                                                        children: [
                                                          const Icon(Icons.traffic, color: Color.fromRGBO(158, 158, 158, 1)),
                                                          const SizedBox(width: 8),
                                                          Text('Traffic', style: Theme.of(context).textTheme.titleMedium),
                                                          const Spacer(),
                                                          _trafficLoading || _incidentsLoading
                                                              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                                                              : IconButton(
                                                                  icon: const Icon(Icons.refresh),
                                                                  tooltip: 'Refresh',
                                                                  onPressed: _fetchTrafficAndIncidents,
                                                                ),
                                                        ],
                                                      ),
                                                    ),
                                                    Divider(height: 1, thickness: 1, color: Colors.grey.shade400),
                                                    SizedBox(height: sectionGap * 1.15),
                                                    Padding(
                                                      padding: EdgeInsets.only(bottom: sectionGap * 0.2),
                                                      child: Text(_trafficInfo, style: const TextStyle(fontSize: 17)),
                                                    ),
                                                    SizedBox(height: sectionGap * 0.3),
                                                    Padding(
                                                      padding: EdgeInsets.only(bottom: sectionGap * 0.2),
                                                      child: Text(
                                                        'Traffic Alerts & Incidents:',
                                                        style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                                                      ),
                                                    ),
                                                    Expanded(
                                                      child: _trafficIncidents.isNotEmpty
                                                          ? ScrollConfiguration(
                                                              behavior: ScrollConfiguration.of(context).copyWith(scrollbars: true),
                                                              child: ListView.builder(
                                                                physics: const AlwaysScrollableScrollPhysics(),
                                                                itemCount: _trafficIncidents.length,
                                                                itemBuilder: (context, index) {
                                                                  final incident = _trafficIncidents[index];
                                                                  return Container(
                                                                    width: double.infinity,
                                                                    margin: EdgeInsets.only(bottom: itemSpacing),
                                                                    padding: EdgeInsets.symmetric(horizontal: itemPadding, vertical: itemSpacing + 1),
                                                                    decoration: BoxDecoration(
                                                                      color: Colors.white,
                                                                      borderRadius: BorderRadius.circular(8),
                                                                    ),
                                                                    child: Column(
                                                                      crossAxisAlignment: CrossAxisAlignment.start,
                                                                      children: [
                                                                        Text(
                                                                          incident['description'] ?? 'Traffic incident',
                                                                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                                                                          maxLines: 2,
                                                                          overflow: TextOverflow.ellipsis,
                                                                        ),
                                                                        if (incident['delay'] > 0)
                                                                          Text('Delay: ${incident['delay']} min', style: const TextStyle(fontSize: 12, color: Colors.red)),
                                                                      ],
                                                                    ),
                                                                  );
                                                                },
                                                              ),
                                                            )
                                                          : Container(
                                                              width: double.infinity,
                                                              padding: const EdgeInsets.all(12),
                                                              decoration: BoxDecoration(
                                                                color: Colors.grey.shade100,
                                                                borderRadius: BorderRadius.circular(8),
                                                              ),
                                                              child: Center(
                                                                child: Text(
                                                                  (_trafficAlert.isEmpty || _trafficAlert == "No alerts")
                                                                      ? 'No alerts or incidents right now'
                                                                      : _trafficAlert,
                                                                  style: TextStyle(
                                                                    fontSize: 14,
                                                                    color: (_trafficAlert.isEmpty || _trafficAlert == "No alerts")
                                                                        ? Colors.grey
                                                                        : Colors.black87,
                                                                    fontWeight: (_trafficAlert.isEmpty || _trafficAlert == "No alerts")
                                                                        ? FontWeight.normal
                                                                        : FontWeight.bold,
                                                                  ),
                                                                  textAlign: TextAlign.center,
                                                                ),
                                                              ),
                                                            ),
                                                    ),
                                                  ],
                                                ),
                                              ),
                                            ),
                                          ),
                                          SizedBox(height: sectionGap * 0.7),
                                          Expanded(
                                            flex: stackCards ? 1 : 1,
                                            child: Card(
                                              margin: EdgeInsets.zero,
                                              elevation: 1.5,
                                              clipBehavior: Clip.antiAlias,
                                              shape: RoundedRectangleBorder(
                                                borderRadius: BorderRadius.circular(16),
                                                side: const BorderSide(color: neutralCardBorder),
                                              ),
                                              color: const Color.fromRGBO(247, 247, 249, 1),
                                              child: Padding(
                                                padding: EdgeInsets.all(cardPadding),
                                                child: Column(
                                                  crossAxisAlignment: CrossAxisAlignment.stretch,
                                                  children: [
                                                    Padding(
                                                      padding: EdgeInsets.only(bottom: sectionGap * 0.25),
                                                      child: Row(
                                                        children: [
                                                          const Icon(Icons.cloud, color: Color.fromRGBO(158, 158, 158, 1)),
                                                          const SizedBox(width: 7),
                                                          Text('Weather', style: Theme.of(context).textTheme.titleMedium),
                                                          const Spacer(),
                                                          _weatherLoading || _forecastLoading
                                                              ? const SizedBox(width: 19, height: 19, child: CircularProgressIndicator(strokeWidth: 2))
                                                              : IconButton(
                                                                  icon: const Icon(Icons.refresh),
                                                                  iconSize: 21,
                                                                  padding: EdgeInsets.zero,
                                                                  constraints: BoxConstraints(minWidth: 30 + itemPadding / 2, minHeight: 30 + itemPadding / 2),
                                                                  visualDensity: VisualDensity.compact,
                                                                  tooltip: 'Refresh',
                                                                  onPressed: _fetchWeatherAndForecast,
                                                                ),
                                                        ],
                                                      ),
                                                    ),
                                                    Divider(height: 1, thickness: 1, color: Colors.grey.shade400),
                                                    SizedBox(
                                                      height: sectionGap * (compactWeatherLayout ? 0.6 : 1.15),
                                                    ),
                                                    Padding(
                                                      padding: EdgeInsets.only(bottom: sectionGap * 0.2),
                                                      child: Text(_weatherInfo, style: const TextStyle(fontSize: 19), maxLines: 1, overflow: TextOverflow.ellipsis),
                                                    ),
                                                    Padding(
                                                      padding: EdgeInsets.only(bottom: sectionGap * 0.2),
                                                      child: Text(_weatherAlert, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis),
                                                    ),
                                                    SizedBox(
                                                      height: sectionGap * (compactWeatherLayout ? 0.65 : 1.35),
                                                    ),
                                                    Padding(
                                                      padding: EdgeInsets.only(bottom: sectionGap * 0.2),
                                                      child: Text('Today\'s Forecast:', style: Theme.of(context).textTheme.titleSmall),
                                                    ),
                                                    Expanded(
                                                      child: _forecast.isNotEmpty
                                                          ? Listener(
                                                              onPointerSignal: _onForecastPointerSignal,
                                                              child: LayoutBuilder(
                                                                builder: (context, constraints) {
                                                                  final double availableHeight = constraints.maxHeight;
                                                                  final double sliderHeight = compactWeatherLayout ? 18.0 : 22.0;
                                                                  final double sliderGap = compactWeatherLayout ? 2.0 : 4.0;
                                                                  final double forecastLaneHeight =
                                                                    (availableHeight - sliderHeight - sliderGap)
                                                                      .clamp(64.0, chipSide + 22)
                                                                      .toDouble();
                                                                  final double chipRenderSide =
                                                                    forecastLaneHeight.clamp(64.0, chipSide).toDouble();
                                                                  final double timeFontSize = (chipRenderSide * 0.17).clamp(9.0, 14.0).toDouble();
                                                                  final double detailFontSize = (chipRenderSide * 0.14).clamp(8.0, 12.0).toDouble();
                                                                  return Column(
                                                                    crossAxisAlignment: CrossAxisAlignment.stretch,
                                                                    children: [
                                                                      SizedBox(
                                                                        height: forecastLaneHeight,
                                                                        child: ListView.separated(
                                                                          controller: _forecastScrollController,
                                                                          primary: false,
                                                                          physics: const AlwaysScrollableScrollPhysics(),
                                                                          scrollDirection: Axis.horizontal,
                                                                          padding: EdgeInsets.zero,
                                                                          itemCount: _forecast.length,
                                                                          separatorBuilder: (_, __) => const SizedBox(width: 10),
                                                                          itemBuilder: (context, index) {
                                                                            final f = _forecast[index];
                                                                            return Center(
                                                                              child: Container(
                                                                                width: chipRenderSide,
                                                                                height: chipRenderSide,
                                                                                padding: EdgeInsets.symmetric(horizontal: itemPadding * 0.5, vertical: itemSpacing + 1),
                                                                                decoration: BoxDecoration(
                                                                                  color: Colors.white,
                                                                                  borderRadius: BorderRadius.circular(10),
                                                                                  border: Border.all(color: Colors.grey.shade400, width: 1),
                                                                                ),
                                                                                child: Column(
                                                                                  mainAxisAlignment: MainAxisAlignment.center,
                                                                                  crossAxisAlignment: CrossAxisAlignment.center,
                                                                                  children: [
                                                                                    Text(
                                                                                      (() {
                                                                                        final dt = f['time'] as DateTime;
                                                                                        final hour = dt.hour == 0 || dt.hour == 12 ? 12 : dt.hour % 12;
                                                                                        final ampm = dt.hour < 12 ? 'AM' : 'PM';
                                                                                        return '$hour $ampm';
                                                                                      })(),
                                                                                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: timeFontSize),
                                                                                    ),
                                                                                    const SizedBox(height: 2),
                                                                                    Text(
                                                                                      (() {
                                                                                        final desc = f['desc'] ?? '';
                                                                                        return desc.isNotEmpty ? '${desc[0].toUpperCase()}${desc.substring(1)}' : '--';
                                                                                      })(),
                                                                                      style: TextStyle(fontSize: detailFontSize),
                                                                                      maxLines: 1,
                                                                                      overflow: TextOverflow.ellipsis,
                                                                                    ),
                                                                                    Text(
                                                                                      f['temp'] != null ? '${f['temp'].toStringAsFixed(1)}°F' : '--',
                                                                                      style: TextStyle(fontSize: detailFontSize),
                                                                                    ),
                                                                                  ],
                                                                                ),
                                                                              ),
                                                                            );
                                                                          },
                                                                        ),
                                                                      ),
                                                                      SizedBox(height: sliderGap),
                                                                      SizedBox(
                                                                        height: sliderHeight,
                                                                        child: SliderTheme(
                                                                          data: SliderTheme.of(context).copyWith(
                                                                            trackHeight: 3,
                                                                            thumbShape: RoundSliderThumbShape(
                                                                              enabledThumbRadius: compactWeatherLayout ? 5 : 6,
                                                                            ),
                                                                            overlayShape: SliderComponentShape.noOverlay,
                                                                            activeTrackColor: Color.fromRGBO(69, 0, 132, 1),
                                                                            inactiveTrackColor: Color.fromRGBO(198, 198, 204, 1),
                                                                            thumbColor: Color.fromRGBO(69, 0, 132, 1),
                                                                          ),
                                                                          child: Slider(
                                                                            min: 0,
                                                                            max: 1,
                                                                            value: _forecastScrollValue,
                                                                            onChanged: _onForecastSliderChanged,
                                                                          ),
                                                                        ),
                                                                      ),
                                                                    ],
                                                                  );
                                                                },
                                                              ),
                                                            )
                                                          : Container(
                                                              width: double.infinity,
                                                              padding: const EdgeInsets.all(12),
                                                              decoration: BoxDecoration(
                                                                color: Colors.grey.shade100,
                                                                borderRadius: BorderRadius.circular(8),
                                                              ),
                                                              child: const Center(
                                                                child: Text('No forecast data available', style: TextStyle(fontSize: 12, color: Colors.grey), textAlign: TextAlign.center),
                                                              ),
                                                            ),
                                                    ),
                                                  ],
                                                ),
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            ),
          ],
        ),
      ),
    );
  }

}
