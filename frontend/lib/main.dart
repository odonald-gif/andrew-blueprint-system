import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'dart:convert';
import 'package:glassmorphism/glassmorphism.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_animate/flutter_animate.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:http/http.dart' as http;
import 'dart:async';

const String API_KEY = "andrew_secure_key_change_me";

String get BASE_URL {
  if (kIsWeb) return "http://localhost:8000/api/v1";
  if (defaultTargetPlatform == TargetPlatform.android) return "http://10.0.2.2:8000/api/v1";
  return "http://localhost:8000/api/v1";
}

String get WS_URL {
  if (kIsWeb) return "ws://localhost:8000/ws";
  if (defaultTargetPlatform == TargetPlatform.android) return "ws://10.0.2.2:8000/ws";
  return "ws://localhost:8000/ws";
}

void main() => runApp(AndrewPremiumApp());

class AndrewPremiumApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Project Andrew: Scrollytelling',
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: Color(0xFF0F172A), // Slate 900
        textTheme: GoogleFonts.interTextTheme(Theme.of(context).textTheme),
      ),
      home: ScrollytellingDashboard(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class ScrollytellingDashboard extends StatefulWidget {
  @override
  _ScrollytellingDashboardState createState() => _ScrollytellingDashboardState();
}

class _ScrollytellingDashboardState extends State<ScrollytellingDashboard> with SingleTickerProviderStateMixin {
  late WebSocketChannel channel;
  
  FlutterTts flutterTts = FlutterTts();
  stt.SpeechToText speech = stt.SpeechToText();
  bool _isListening = false;
  String donnaMessage = "Good morning. I've already optimized your day.";
  Color statusColor = Colors.tealAccent;
  TextEditingController _chatController = TextEditingController();
  
  bool hasInterviewAlert = false; // Real alert
  bool isBiometricLocked = false; // Biometric Privacy Vault
  bool hasPendingProposal = false; // Interactive Handshake
  bool hasShadowMessage = false; // Donna Shadow Mode (Swipe to send)
  int energyScore = 85; // Motion Engine Energy Level
  
  // Dynamic Bar Pulses: Green(Money), Blue(GitHub), Orange(Interview)
  Color dynamicBarColor = Colors.greenAccent; 
  String dynamicBarText = "Andrew Core Online";
  
  Map<String, dynamic> revenueData = {
    "projected_earnings": 0.00,
    "bounties_won": 0.00,
    "saas_income": 0.00
  };

  List<dynamic> pendingDrafts = [];

  List<dynamic> scheduleItems = [];

  Color _getColorForType(String type, int energy) {
    if (type == "personal") return Colors.greenAccent;
    if (type == "career") return Colors.purpleAccent;
    if (energy > 80) return Colors.redAccent;
    if (energy > 60) return Colors.orangeAccent;
    return Colors.blueAccent;
  }

  Widget _buildTimelineItem(int index) {
    final item = scheduleItems[index];
    final color = _getColorForType(item['type'] ?? "work", item['energy']);
    
    return Padding(
      padding: const EdgeInsets.only(bottom: 25.0),
      child: GlassmorphicContainer(
        width: double.infinity,
        height: item.containsKey('note') ? 140 : 100,
        borderRadius: 20,
        blur: 15,
        alignment: Alignment.center,
        border: 1,
        linearGradient: LinearGradient(
          colors: [color.withOpacity(0.2), color.withOpacity(0.05)],
        ),
        borderGradient: LinearGradient(
          colors: [color.withOpacity(0.5), Colors.transparent],
        ),
        child: Padding(
          padding: const EdgeInsets.all(15.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(item['time'], style: TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold)),
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(color: color.withOpacity(0.3), borderRadius: BorderRadius.circular(10)),
                    child: Text("Energy: ${item['energy']}", style: TextStyle(color: color, fontSize: 10)),
                  )
                ],
              ),
              SizedBox(height: 8),
              Text(item['title'], style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              if (item.containsKey('note')) ...[
                SizedBox(height: 10),
                Row(
                  children: [
                    Icon(Icons.notes, color: Colors.white54, size: 14),
                    SizedBox(width: 5),
                    Expanded(child: Text(item['note'], style: TextStyle(color: Colors.white70, fontSize: 12, fontStyle: FontStyle.italic))),
                  ],
                )
              ]
            ],
          ),
        ),
      ).animate().fade(delay: (100 * index).ms).slideY(begin: 0.2, end: 0),
    );
  }

  Timer? _pollingTimer;

  @override
  void initState() {
    super.initState();
    _initVoice();
    _fetchDashboardSummary();
    
    // Poll every 10 seconds
    _pollingTimer = Timer.periodic(Duration(seconds: 10), (timer) {
      _fetchDashboardSummary();
    });

    // Connect to Backend Nervous System
    channel = WebSocketChannel.connect(Uri.parse(WS_URL));
    channel.stream.listen((message) {
      final data = jsonDecode(message);
      setState(() {
        if (data['type'] == 'status_update') {
          statusColor = Colors.orangeAccent;
          donnaMessage = "Status update received.";
          _speak(donnaMessage);
        }
      });
    });
  }

  Future<void> _fetchDashboardSummary() async {
    try {
      final response = await http.get(
        Uri.parse('$BASE_URL/dashboard/summary'),
        headers: {'X-Andrew-Key': API_KEY},
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          revenueData = data['revenueData'];
          pendingDrafts = data['pendingDrafts'];
          scheduleItems = data['scheduleItems'];
          
          if (pendingDrafts.isNotEmpty) {
            hasShadowMessage = true;
          } else {
            hasShadowMessage = false;
          }
        });
      }
    } catch (e) {
      print("Error fetching dashboard summary: \$e");
    }
  }

  void _initVoice() async {
    try {
      await flutterTts.setSharedInstance(true);
      await flutterTts.setIosAudioCategory(IosTextToSpeechAudioCategory.ambient,
          [
            IosTextToSpeechAudioCategoryOptions.allowBluetooth,
            IosTextToSpeechAudioCategoryOptions.allowBluetoothA2DP,
            IosTextToSpeechAudioCategoryOptions.mixWithOthers,
          ],
          IosTextToSpeechAudioMode.voicePrompt
      );
    } catch (e) {
      print("TTS setup error (expected on web): \$e");
    }
    await flutterTts.setLanguage("en-GB");
    await flutterTts.setPitch(0.9); // Deep, professional tone
    await flutterTts.setSpeechRate(0.5);
  }

  void _speak(String text) async {
    await flutterTts.speak(text);
  }

  void _listen() async {
    if (!_isListening) {
      bool available = await speech.initialize();
      if (available) {
        setState(() => _isListening = true);
        speech.listen(onResult: (val) {
          if (val.hasConfidenceRating && val.confidence > 0.8) {
            channel.sink.add(jsonEncode({"type": "voice_input", "text": val.recognizedWords}));
            setState(() => _isListening = false);
            speech.stop();
          }
        });
      }
    }
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    channel.sink.close();
    flutterTts.stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.record_voice_over, color: Colors.blueAccent),
            tooltip: "Mock Interview Mirror",
            onPressed: () {
              // Trigger microphone for Mock Interview simulation
            },
          ),
          IconButton(
            icon: Icon(Icons.camera_alt_outlined, color: Colors.greenAccent),
            tooltip: "Give Andrew Eyes",
            onPressed: () {
              // Trigger Camera API and send frame buffer to Oracle Server
              channel.sink.add(jsonEncode({"type": "vision_request", "action": "Analyzing visual input..."}));
              setState(() {
                dynamicBarText = "VISION ONLINE";
                dynamicBarColor = Colors.greenAccent;
              });
            },
          ),
          IconButton(
            icon: Icon(_isListening ? Icons.mic : Icons.mic_none, color: _isListening ? Colors.redAccent : Colors.white70),
            onPressed: _listen,
          )
        ],
      ),
      body: Stack(
        children: [
          // Scrollytelling ambient gradient based on Energy Score
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: energyScore > 70 
                  ? [Color(0xFF0F172A), Color(0xFF0D47A1)] // High Energy (Blue/Teal)
                  : [Color(0xFF0F172A), Color(0xFF4E342E)], // Low Energy (Warm/Brown)
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              )
            ),
          ),
          
          // The itel S26 Ultra Dynamic Bar (Color Pulses)
          Align(
            alignment: Alignment.topCenter,
            child: Container(
              margin: EdgeInsets.only(top: 40),
              width: 220,
              height: 35,
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.8),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: dynamicBarColor.withOpacity(0.5), width: 2)
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.bolt, color: dynamicBarColor, size: 16),
                  SizedBox(width: 5),
                  Text(dynamicBarText, style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ),
          
          // Interview Summon Alert
          if (hasInterviewAlert)
            Align(
              alignment: Alignment.topCenter,
              child: Padding(
                padding: const EdgeInsets.only(top: 90.0, left: 20, right: 20),
                child: Container(
                  width: double.infinity,
                  padding: EdgeInsets.symmetric(vertical: 10, horizontal: 15),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withOpacity(0.9),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.warning_amber_rounded, color: Colors.white),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text("🚨 INTERVIEW READY: Upwork Client booked for 2 PM.", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12)),
                      )
                    ],
                  ),
                ),
              ),
            ),

          
          // Main Scroll View
          ListView.builder(
            padding: EdgeInsets.only(top: 180, bottom: 150),
            itemCount: scheduleItems.length,
            itemBuilder: (context, index) => _buildTimelineItem(index),
          ),

          // Wealth Dashboard (Top)
          Align(
            alignment: Alignment.topCenter,
            child: Padding(
              padding: const EdgeInsets.only(top: 130.0, left: 20, right: 20),
              child: GlassmorphicContainer(
                width: double.infinity,
                height: 100,
                borderRadius: 20,
                blur: 20,
                alignment: Alignment.center,
                border: 2,
                linearGradient: LinearGradient(
                  colors: [Colors.greenAccent.withOpacity(0.15), Colors.greenAccent.withOpacity(0.05)],
                ),
                borderGradient: LinearGradient(
                  colors: [Colors.greenAccent.withOpacity(0.5), Colors.transparent],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text("\$${revenueData['projected_earnings']}", style: TextStyle(color: Colors.greenAccent, fontSize: 24, fontWeight: FontWeight.bold)),
                        Text("Projected Earnings", style: TextStyle(color: Colors.white70, fontSize: 12)),
                      ],
                    ),
                    Container(width: 1, height: 60, color: Colors.white24),
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text("\$${revenueData['bounties_won']}", style: TextStyle(color: Colors.greenAccent, fontSize: 18, fontWeight: FontWeight.bold)),
                        Text("Bounties", style: TextStyle(color: Colors.white70, fontSize: 12)),
                      ],
                    ),
                    Container(width: 1, height: 60, color: Colors.white24),
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text("\$${revenueData['saas_income']}", style: TextStyle(color: Colors.greenAccent, fontSize: 18, fontWeight: FontWeight.bold)),
                        Text("Passive SaaS", style: TextStyle(color: Colors.white70, fontSize: 12)),
                      ],
                    ),
                  ],
                ),
              ).animate().fade().slideY(begin: -0.2, end: 0),
            ),
          ),
          
          // Relocation Dashboard (Japa Blueprint)
          Align(
            alignment: Alignment.topCenter,
            child: Padding(
              padding: const EdgeInsets.only(top: 240.0, left: 20, right: 20),
              child: GlassmorphicContainer(
                width: double.infinity,
                height: 80,
                borderRadius: 15,
                blur: 15,
                alignment: Alignment.center,
                border: 1,
                linearGradient: LinearGradient(
                  colors: [Colors.blueAccent.withOpacity(0.1), Colors.purpleAccent.withOpacity(0.05)],
                ),
                borderGradient: LinearGradient(
                  colors: [Colors.blueAccent, Colors.transparent],
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text("\$3,520 USDT", style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                        Text("Relocation Fund", style: TextStyle(color: Colors.white70, fontSize: 12)),
                      ],
                    ),
                    Container(width: 1, height: 40, color: Colors.white24),
                    Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.school, color: Colors.orangeAccent),
                        Text("DAAD Scanned", style: TextStyle(color: Colors.white70, fontSize: 12)),
                      ],
                    ),
                  ],
                )
              ).animate().fade(delay: 300.ms),
            ),
          ),
          
          // The Handshake (Observer-Actuator Notification)
          if (hasPendingProposal)
            Align(
              alignment: Alignment.topCenter,
              child: Padding(
                padding: const EdgeInsets.only(top: 330.0, left: 20, right: 20),
                child: Container(
                  width: double.infinity,
                  padding: EdgeInsets.all(15),
                  decoration: BoxDecoration(
                    color: Colors.blueGrey[900]?.withOpacity(0.95),
                    borderRadius: BorderRadius.circular(15),
                    border: Border.all(color: Colors.blueAccent.withOpacity(0.5), width: 1),
                  ),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.mail_outline, color: Colors.blueAccent),
                          SizedBox(width: 10),
                          Expanded(child: Text("Proposal Drafted", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold))),
                        ],
                      ),
                      SizedBox(height: 10),
                      Text("Donald, I found a Remote Cloud Migration internship. I've drafted a proposal based on your AWS school lab. Submit it?", style: TextStyle(color: Colors.white70, fontSize: 13)),
                      SizedBox(height: 15),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          ElevatedButton(
                            style: ElevatedButton.styleFrom(backgroundColor: Colors.greenAccent, foregroundColor: Colors.black),
                            onPressed: () {
                              setState(() {
                                hasPendingProposal = false;
                                donnaMessage = "Sent. I've connected with the Hiring Manager on LinkedIn.";
                                _speak(donnaMessage);
                              });
                            },
                            child: Text("Yes"),
                          ),
                          OutlinedButton(
                            style: OutlinedButton.styleFrom(side: BorderSide(color: Colors.redAccent), foregroundColor: Colors.redAccent),
                            onPressed: () { setState(() { hasPendingProposal = false; }); },
                            child: Text("No"),
                          ),
                          OutlinedButton(
                            style: OutlinedButton.styleFrom(side: BorderSide(color: Colors.white54), foregroundColor: Colors.white),
                            onPressed: () { },
                            child: Text("Edit"),
                          ),
                        ],
                      )
                    ],
                  ),
                ).animate().slideX(begin: 1.0, end: 0, delay: 500.ms),
              ),
            ),
            
          // Shadow Mode: WhatsApp Swipe-to-Send
          if (hasShadowMessage)
            Align(
              alignment: Alignment.topCenter,
              child: Padding(
                padding: const EdgeInsets.only(top: 480.0, left: 20, right: 20),
                child: Dismissible(
                  key: Key('shadow_message'),
                  background: Container(color: Colors.green, alignment: Alignment.centerLeft, padding: EdgeInsets.only(left: 20), child: Icon(Icons.send, color: Colors.white)),
                  secondaryBackground: Container(color: Colors.orange, alignment: Alignment.centerRight, padding: EdgeInsets.only(right: 20), child: Icon(Icons.edit, color: Colors.white)),
                  onDismissed: (direction) {
                    setState(() { hasShadowMessage = false; });
                    if (direction == DismissDirection.startToEnd) {
                      _speak("Sent exactly as you would have.");
                    }
                  },
                  child: Container(
                    width: double.infinity,
                    padding: EdgeInsets.all(15),
                    decoration: BoxDecoration(
                      color: Colors.black87,
                      borderRadius: BorderRadius.circular(15),
                      border: Border.all(color: Colors.purpleAccent.withOpacity(0.5), width: 1),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.visibility, color: Colors.purpleAccent, size: 16),
                            SizedBox(width: 5),
                            Text("SHADOW MODE (WhatsApp)", style: TextStyle(color: Colors.purpleAccent, fontSize: 10, fontWeight: FontWeight.bold)),
                          ],
                        ),
                        SizedBox(height: 8),
                        Text("From: \${pendingDrafts.isNotEmpty ? pendingDrafts[0]['sender'] : 'Unknown'}", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12)),
                        SizedBox(height: 4),
                        Text("Draft: '\${pendingDrafts.isNotEmpty ? pendingDrafts[0]['message'] : ''}'", style: TextStyle(color: Colors.white70, fontStyle: FontStyle.italic, fontSize: 13)),
                        SizedBox(height: 8),
                        Text("Swipe Right to Send → | ← Swipe Left to Edit", style: TextStyle(color: Colors.white54, fontSize: 10)),
                      ],
                    ),
                  ),
                ).animate().fade(delay: 600.ms),
              ),
            ),

          // Floating Donna Persona Commentator
          Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: const EdgeInsets.only(left: 20.0, right: 20.0, bottom: 20.0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (pendingDrafts.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 15.0),
                      child: GlassmorphicContainer(
                        width: double.infinity,
                        height: 60,
                        borderRadius: 20,
                        blur: 15,
                        alignment: Alignment.center,
                        border: 1,
                        linearGradient: LinearGradient(
                          colors: [Colors.redAccent.withOpacity(0.2), Colors.redAccent.withOpacity(0.05)],
                        ),
                        borderGradient: LinearGradient(
                          colors: [Colors.redAccent, Colors.transparent],
                        ),
                        child: ListTile(
                          leading: Icon(Icons.warning_amber_rounded, color: Colors.white),
                          title: Text("${pendingDrafts.length} Pending Approval(s)", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                          trailing: IconButton(
                            icon: Icon(Icons.check_circle, color: Colors.greenAccent),
                            onPressed: () {
                              setState(() {
                                pendingDrafts.clear();
                                _speak("Drafts approved and sent.");
                              });
                            },
                          ),
                        ),
                      ).animate().scale(delay: 500.ms),
                    ),
                  GlassmorphicContainer(
                    width: double.infinity,
                    height: 120, // Taller to accommodate input
                    borderRadius: 30,
                    blur: 20,
                    alignment: Alignment.center,
                    border: 2,
                    linearGradient: LinearGradient(
                      colors: [statusColor.withOpacity(0.1), statusColor.withOpacity(0.05)],
                    ),
                    borderGradient: LinearGradient(
                      colors: [statusColor.withOpacity(0.5), Colors.transparent],
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.graphic_eq, color: statusColor)
                              .animate(onPlay: (controller) => controller.repeat(reverse: true))
                              .scaleXY(begin: 1.0, end: 1.2, duration: 800.ms),
                              SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  donnaMessage,
                                  style: TextStyle(color: Colors.white, fontSize: 13, fontStyle: FontStyle.italic),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ).animate().fade(),
                              ),
                            ],
                          ),
                          Container(
                            height: 45,
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.05),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Row(
                              children: [
                                Expanded(
                                  child: TextField(
                                    controller: _chatController,
                                    style: TextStyle(color: Colors.white, fontSize: 14),
                                    decoration: InputDecoration(
                                      hintText: "Briefing Console...",
                                      hintStyle: TextStyle(color: Colors.white38),
                                      border: InputBorder.none,
                                      contentPadding: EdgeInsets.symmetric(horizontal: 15),
                                    ),
                                    onSubmitted: (val) {
                                      setState(() {
                                        if (val.toLowerCase().contains("thanks") || val.toLowerCase().contains("grateful")) {
                                            donnaMessage = "You're welcome. I knew exactly what you needed help with. Honestly, what would you do without me?";
                                        } else {
                                            donnaMessage = "Noted. I'll update the records.";
                                        }
                                        _chatController.clear();
                                        _speak(donnaMessage);
                                      });
                                    },
                                  ),
                                ),
                                IconButton(
                                  icon: Icon(Icons.send, color: Colors.white54, size: 20),
                                  onPressed: () {
                                    // Trigger the submit logic
                                    setState(() {
                                      donnaMessage = "You're welcome. I knew exactly what you needed help with. Honestly, what would you do without me?";
                                      _chatController.clear();
                                      _speak(donnaMessage);
                                    });
                                  },
                                )
                              ],
                            ),
                          )
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          
          // Privacy Vault: Biometric Dead-Drop Overlay
          if (isBiometricLocked)
            Container(
              color: Colors.black.withOpacity(0.95),
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.face, color: Colors.blueAccent, size: 100),
                    SizedBox(height: 20),
                    Text("Biometric Dead-Drop Active", style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
                    SizedBox(height: 10),
                    Text("Andrew requires FaceID to process sensitive request.", style: TextStyle(color: Colors.white70, fontSize: 14)),
                    SizedBox(height: 40),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent),
                      onPressed: () {
                        setState(() {
                          isBiometricLocked = false;
                        });
                      },
                      child: Text("Simulate FaceID Unlock", style: TextStyle(color: Colors.white)),
                    )
                  ],
                )
              )
            )

        ],
      ),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Colors.tealAccent,
        child: Icon(Icons.security, color: Colors.black),
        onPressed: () {
          setState(() {
             isBiometricLocked = true;
          });
        },
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.endFloat,
    );
  }
}
