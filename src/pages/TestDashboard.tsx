import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, CheckCircle, Clock, Loader } from 'lucide-react';

interface CampaignOption {
  id: string;
  name: string;
}

interface Lead {
  id: string;
  name: string;
  email: string;
  company?: string;
  source?: string;
}

interface IntentSignalItem {
  id: string;
  company_id: string;
  company_url?: string;
  signal_type: string;
  source: string;
  strength: number;
  lead_id?: string | null;
  is_openable?: boolean;
}

interface ScanResult {
  scan_id: string;
  status: string;
  progress: number;
  results?: {
    companies_scanned: number;
    companies_found: number;
    leads_created: number;
    signals_detected: number;
  };
  error?: string;
}

interface ConnectionResult {
  connection_id: string;
  lead_id: string;
  status: string;
  message?: string;
  template_set?: string;
}

interface AnalyticsResult {
  sequence_id: string;
  leads_enrolled: number;
  connections_sent: number;
  connections_accepted: number;
  messages_sent: number;
  replies_received: number;
  engagement_rate: number;
}

const API_BASE = 'http://localhost:8000';

// Helper to get authorization header
const getAuthHeader = () => {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    throw new Error('No authentication token found. Please log in first.');
  }
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
};

export default function TestDashboard() {
  const [campaigns, setCampaigns] = useState<CampaignOption[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState('');
  const [selectedLead, setSelectedLead] = useState('');
  
  // Phase 2 States
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [scanLoading, setScanLoading] = useState(false);
  const [scheduleFrequency, setScheduleFrequency] = useState('daily');
  const [scheduleTime, setScheduleTime] = useState('02:00');
  const [services, setServices] = useState<string[]>(['Software Development', 'Web Development']);
  const [locations, setLocations] = useState<string[]>(['India']);
  const [newService, setNewService] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [signals, setSignals] = useState<IntentSignalItem[]>([]);
  
  // Phase 5 States
  const [connectionResult, setConnectionResult] = useState<ConnectionResult | null>(null);
  const [connectionLoading, setConnectionLoading] = useState(false);
  const [linkedinConnections, setLinkedinConnections] = useState<any[]>([]);
  const [templateSet, setTemplateSet] = useState<'standard' | 'aggressive' | 'consultative' | 'value_first'>('standard');
  const [profileUrl, setProfileUrl] = useState('');
  const [profileName, setProfileName] = useState('');
  const [connectionMessage, setConnectionMessage] = useState('Hi {name}! I help companies like {company} with {service}. Would love to connect.');
  const [analytics, setAnalytics] = useState<AnalyticsResult | null>(null);
  const [messageText, setMessageText] = useState('');
  
  // Check authentication
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      console.warn('No authentication token found! User may not be logged in.');
    }
  }, []);
  
  // Load campaigns on mount
  useEffect(() => {
    console.log('TestDashboard mounted, loading campaigns...');
    loadCampaigns();
  }, []);

  // Load leads when campaign changes
  useEffect(() => {
    if (selectedCampaign) {
      console.log(`Campaign selected: ${selectedCampaign}, loading leads...`);
      loadLeads();
    }
  }, [selectedCampaign]);

  const loadCampaigns = async () => {
    try {
      const headers = getAuthHeader();
      console.log('Loading campaigns with auth header...');
      const response = await fetch(`${API_BASE}/api/v1/campaigns?skip=0&limit=100`, {
        headers
      });
      console.log(`Campaigns response: ${response.status}`);
      if (response.ok) {
        const data = await response.json();
        console.log(`Loaded ${data.length} campaigns:`, data);
        setCampaigns(data);
        if (data.length > 0) {
          setSelectedCampaign(data[0].id);
        }
      } else {
        const error = await response.text();
        console.error('Failed to load campaigns:', response.status, error);
      }
    } catch (error) {
      console.error('Error loading campaigns:', error);
    }
  };

  const loadLeads = async () => {
    try {
      console.log(`Loading leads for campaign: ${selectedCampaign}`);
      const response = await fetch(`${API_BASE}/api/v1/leads/campaign/${selectedCampaign}?skip=0&limit=100`, {
        headers: getAuthHeader()
      });
      console.log(`Leads response: ${response.status}`);
      if (response.ok) {
        const data = await response.json();
        console.log(`Loaded ${Array.isArray(data) ? data.length : 0} leads:`, data);
        setLeads(Array.isArray(data) ? data : []);
        if (data.length > 0) {
          setSelectedLead(data[0].id);
        }
      } else {
        const error = await response.text();
        console.error('Failed to load leads:', response.status, error);
        setLeads([]);
      }
    } catch (error) {
      console.error('Error loading leads:', error);
      setLeads([]);
    }
  };

  // PHASE 2: Start Intent Scan
  const handleStartScan = async () => {
    setScanLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/v1/leads/run-intent-scan`, {
        method: 'POST',
        headers: getAuthHeader(),
        body: JSON.stringify({
          campaign_ids: [selectedCampaign],
          services: services,
          locations: locations
        })
      });
      const data = await response.json();
      console.log('Scan response:', data);
      setScanResult(data);
      
      // Poll for progress
      if (data.scan_id) {
        pollScanProgress(data.scan_id);
      }
    } catch (error) {
      console.error('Error starting scan:', error);
      setScanResult({ scan_id: '', status: 'error', progress: 0, error: String(error) });
    } finally {
      setScanLoading(false);
    }
  };

  const pollScanProgress = async (scanId: string) => {
    const maxAttempts = 12; // 60 seconds
    let attempts = 0;

    const poll = setInterval(async () => {
      attempts++;
      try {
        const response = await fetch(`${API_BASE}/api/v1/leads/scan-status?scan_id=${scanId}`, {
          headers: getAuthHeader()
        });
        if (!response.ok) {
          console.error(`Poll failed with status ${response.status}`);
          return;
        }
        const data = await response.json();
        console.log('Scan status response:', data);
        
        // Map backend response to UI state
        setScanResult({
          scan_id: data.scan_id || scanId,
          status: data.status || 'running',
          progress: 50, // Backend doesn't provide progress, so estimate
          results: data.summary
        });

        if (data.status === 'completed' || data.status === 'failed' || attempts >= maxAttempts) {
          clearInterval(poll);
          // Load signals after scan completes
          if (data.status === 'completed') {
            loadSignals();
          }
        }
      } catch (error) {
        console.error('Error polling scan progress:', error);
        clearInterval(poll);
      }
    }, 5000); // Check every 5 seconds
  };

  const loadSignals = async () => {
    try {
      console.log(`Loading signals for campaign: ${selectedCampaign}`);
      const response = await fetch(`${API_BASE}/api/v1/leads/intent-signals?campaign_id=${selectedCampaign}&limit=50`, {
        headers: getAuthHeader()
      });
      console.log(`Signals response: ${response.status}`);
      if (response.ok) {
        const data = await response.json();
        console.log(`Loaded ${Array.isArray(data) ? data.length : '?'} signals:`, data);
        setSignals(Array.isArray(data) ? data : []);
        await loadLeads();
      } else {
        // Endpoint not implemented yet
        console.log('Intent signals endpoint not implemented yet');
        setSignals([]);
      }
    } catch (error) {
      console.error('Error loading signals:', error);
      setSignals([]);
    }
  };

  const handleSetupSchedule = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/leads/intent-scan/schedule`, {
        method: 'POST',
        headers: getAuthHeader(),
        body: JSON.stringify({
          campaign_ids: [selectedCampaign],
          frequency: scheduleFrequency,
          scheduled_time: scheduleTime
        })
      });
      const data = await response.json();
      alert(`Schedule created: ${data.message || data.detail || 'Success'}`);
    } catch (error) {
      alert(`Error: ${error}`);
    }
  };

  // For now, LinkedIn handlers are commented out since endpoints aren't implemented
  // const handleStartSequence = async () => { ... };
  // const loadLinkedinConnections = async () => { ... };
  // const handleSendMessage = async () => { ... };
  // const handleMarkReplied = async () => { ... };
  // const loadAnalytics = async () => { ... };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Testing Dashboard</h1>
          <p className="text-slate-600">Test Phase 2 (Intent Monitoring) & Phase 5 (LinkedIn Outreach)</p>
        </div>

        {/* Campaign & Lead Selection */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Setup</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Select Campaign</label>
              <select
                value={selectedCampaign}
                onChange={(e) => setSelectedCampaign(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">
                  {campaigns.length === 0 ? 'No campaigns available' : 'Select a campaign...'}
                </option>
                {campaigns.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Select Lead (for LinkedIn)</label>
              <select
                value={selectedLead}
                onChange={(e) => setSelectedLead(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">
                  {leads.length === 0 ? 'No leads available for this campaign' : 'Select a lead...'}
                </option>
                {leads.map(l => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        <Tabs defaultValue="phase2" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="phase2">Phase 2: Buyer Intent Discovery</TabsTrigger>
            <TabsTrigger value="phase5">Phase 5: LinkedIn Outreach</TabsTrigger>
          </TabsList>

          {/* PHASE 2: BUYER INTENT DISCOVERY */}
          <TabsContent value="phase2" className="space-y-6">
            {/* Configure Scan Parameters */}
            <Card>
              <CardHeader>
                <CardTitle>Find Companies Seeking Our Services</CardTitle>
                <CardDescription>Search for companies with buyer intent signals (RFP, partnerships, digital transformation)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-slate-700">Services to Search</label>
                  <div className="flex flex-wrap gap-2 mt-2 mb-2">
                    {services.map((service, idx) => (
                      <div key={idx} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                        {service}
                        <button
                          onClick={() => setServices(services.filter((_, i) => i !== idx))}
                          className="ml-1 hover:text-red-600"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      placeholder="E.g., Software Development, Web Design, Mobile App, etc."
                      value={newService}
                      onChange={(e) => setNewService(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && newService.trim()) {
                          setServices([...services, newService.trim()]);
                          setNewService('');
                        }
                      }}
                    />
                    <Button
                      onClick={() => {
                        if (newService.trim()) {
                          setServices([...services, newService.trim()]);
                          setNewService('');
                        }
                      }}
                      variant="outline"
                    >
                      Add
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">Target Locations</label>
                  <div className="flex flex-wrap gap-2 mt-2 mb-2">
                    {locations.map((location, idx) => (
                      <div key={idx} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm flex items-center gap-2">
                        {location}
                        <button
                          onClick={() => setLocations(locations.filter((_, i) => i !== idx))}
                          className="ml-1 hover:text-red-600"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      placeholder="E.g., India, USA, UK, etc."
                      value={newLocation}
                      onChange={(e) => setNewLocation(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && newLocation.trim()) {
                          setLocations([...locations, newLocation.trim()]);
                          setNewLocation('');
                        }
                      }}
                    />
                    <Button
                      onClick={() => {
                        if (newLocation.trim()) {
                          setLocations([...locations, newLocation.trim()]);
                          setNewLocation('');
                        }
                      }}
                      variant="outline"
                    >
                      Add
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Start Scan */}
            <Card>
              <CardHeader>
                <CardTitle>Start Buyer Intent Discovery Scan</CardTitle>
                <CardDescription>Search for companies seeking partners or posting RFPs for these services</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-sm">
                  <p className="font-semibold text-slate-900 mb-2">🎯 Discovery Configuration:</p>
                  <p className="text-slate-600">Services to Offer: <span className="font-mono text-slate-900">{services.join(', ')}</span></p>
                  <p className="text-slate-600">Target Markets: <span className="font-mono text-slate-900">{locations.join(', ')}</span></p>
                </div>
                
                <Button
                  onClick={handleStartScan}
                  disabled={scanLoading || !selectedCampaign}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  size="lg"
                >
                  {scanLoading ? (
                    <>
                      <Loader className="mr-2 h-4 w-4 animate-spin" />
                      Discovering...
                    </>
                  ) : (
                    'Start Intent Scan'
                  )}
                </Button>

                {scanResult && (
                  <div className={`p-4 rounded-lg border-2 ${
                    scanResult.status === 'completed' ? 'border-green-200 bg-green-50' :
                    scanResult.status === 'running' ? 'border-blue-200 bg-blue-50' :
                    scanResult.status === 'failed' ? 'border-red-200 bg-red-50' :
                    'border-slate-200 bg-slate-50'
                  }`}>
                    <div className="flex items-start gap-3">
                      {scanResult.status === 'completed' && <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />}
                      {scanResult.status === 'running' && <Clock className="h-5 w-5 text-blue-600 mt-0.5 animate-spin" />}
                      {scanResult.status === 'failed' && <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />}
                      
                      <div className="flex-1">
                        <h3 className="font-semibold text-slate-900">Status: {scanResult.status}</h3>
                        <p className="text-sm text-slate-600">Scan ID: {scanResult.scan_id?.substring(0, 8)}...</p>
                        
                        {scanResult.progress > 0 && (
                          <div className="mt-2">
                            <div className="w-full bg-slate-200 rounded-full h-2">
                              <div 
                                className="bg-blue-600 h-2 rounded-full transition-all" 
                                style={{ width: `${scanResult.progress}%` }}
                              ></div>
                            </div>
                            <p className="text-xs text-slate-600 mt-1">{scanResult.progress}% complete</p>
                          </div>
                        )}

                        {scanResult.results && (
                          <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                            <div className="bg-white p-2 rounded border border-slate-200">
                              <p className="text-slate-600">Companies Found</p>
                              <p className="font-bold text-lg text-slate-900">{scanResult.results.companies_found}</p>
                            </div>
                            <div className="bg-white p-2 rounded border border-slate-200">
                              <p className="text-slate-600">Leads Created</p>
                              <p className="font-bold text-lg text-slate-900">{scanResult.results.leads_created}</p>
                            </div>
                            <div className="bg-white p-2 rounded border border-slate-200">
                              <p className="text-slate-600">Signals Detected</p>
                              <p className="font-bold text-lg text-slate-900">{scanResult.results.signals_detected}</p>
                            </div>
                          </div>
                        )}

                        {scanResult.error && (
                          <p className="text-sm text-red-600 mt-2">{scanResult.error}</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* View Signals */}
            <Card>
              <CardHeader>
                <CardTitle>Buyer Intent Signals Detected</CardTitle>
                <CardDescription>Companies seeking our services (RFP, partnerships, digital transformation, funding)</CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={loadSignals}
                  variant="outline"
                  className="mb-4"
                >
                  Refresh Signals
                </Button>

                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {signals.length > 0 ? (
                    signals.map((signal, idx) => (
                      <div key={idx} className="p-3 border border-slate-200 rounded-lg bg-slate-50 hover:bg-slate-100">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="font-semibold text-slate-900">🎯 {signal.company_id}</p>
                            <p className="text-sm text-slate-600">Signal: {signal.signal_type} ({signal.source})</p>
                            {signal.lead_id ? (
                              <div className="mt-2">
                                <Link to={`/lead/${signal.lead_id}`}>
                                  <Button size="sm" variant="outline">Open Lead</Button>
                                </Link>
                              </div>
                            ) : (
                              <p className="text-xs text-slate-500 mt-2">Lead not created yet for this signal.</p>
                            )}
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-green-600">{(signal.strength * 100).toFixed(0)}%</p>
                            <p className="text-xs text-slate-500">Buyer Intent</p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-slate-500 py-8">No buyer signals detected. Run a discovery scan first.</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Setup Schedule */}
            <Card>
              <CardHeader>
                <CardTitle>Setup Recurring Discovery</CardTitle>
                <CardDescription>Automatically scan for new buyer intent signals</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Frequency</label>
                  <select
                    value={scheduleFrequency}
                    onChange={(e) => setScheduleFrequency(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md"
                  >
                    <option value="hourly">Hourly</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Scheduled Time (UTC)</label>
                  <input
                    type="time"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md"
                  />
                </div>

                <Button
                  onClick={handleSetupSchedule}
                  className="w-full bg-green-600 hover:bg-green-700"
                >
                  Setup Schedule
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* PHASE 5: LINKEDIN OUTREACH */}
          <TabsContent value="phase5" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Phase 5: LinkedIn Outreach</CardTitle>
                <CardDescription>LinkedIn automation features</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-6 bg-red-50 border-2 border-red-200 rounded-lg">
                  <AlertCircle className="h-8 w-8 text-red-600 mb-2" />
                  <h3 className="text-lg font-semibold text-red-900 mb-2">Not Yet Implemented</h3>
                  <p className="text-red-800">The LinkedIn automation endpoints are not yet implemented in the backend. Phase 5 testing will be available in a future update.</p>
                  <p className="text-red-700 text-sm mt-4">Expected endpoints:</p>
                  <ul className="text-red-700 text-sm list-disc list-inside mt-2">
                    <li>POST /leads/linkedin/sequence/start</li>
                    <li>GET /leads/linkedin/connections</li>
                    <li>POST /leads/linkedin/message/send</li>
                    <li>GET /leads/linkedin/sequence/{'{sequence_id}'}/analytics</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
