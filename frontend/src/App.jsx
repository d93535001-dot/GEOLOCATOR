import React, { useState } from 'react';
import axios from 'axios';
import { Upload, MapPin, Activity, Settings, Link as LinkIcon, Camera, Map, AlertCircle, RefreshCw } from 'lucide-react';
import LightPillar from './components/reactbits/LightPillar';
import DecryptedText from './components/reactbits/DecryptedText';
import FuzzyText from './components/reactbits/FuzzyText';
import PillNav from './components/reactbits/PillNav';
import ClickSpark from './components/reactbits/ClickSpark';
import OrbitImages from './components/reactbits/OrbitImages';
import TextType from './components/reactbits/TextType';
import StickerPeel from './components/reactbits/StickerPeel';
import FluidGlass from './components/reactbits/FluidGlass';

export default function App() {
  const [activeTab, setActiveTab] = useState("Анализ");
  const [file, setFile] = useState(null);
  const [shadowRatio, setShadowRatio] = useState("");
  const [timestamp, setTimestamp] = useState("");
  const [longitude, setLongitude] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState("Система готова. Ожидание данных...");

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setLogs("Запуск конвейера анализа...\nВыполнение детекции объектов (YOLO)...\nРаспознавание текста (EasyOCR)...");

    const formData = new FormData();
    formData.append("file", file);
    if (shadowRatio !== "") formData.append("shadow_ratio", shadowRatio);
    if (timestamp !== "") formData.append("timestamp", timestamp);
    if (longitude !== "") formData.append("longitude", longitude);

    try {
      const response = await axios.post("/api/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setResults(response.data);
      setLogs("Анализ завершен. Данные успешно извлечены.");
    } catch (err) {
      console.error(err);
      setLogs(`Ошибка: ${err.message}`);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResults(null);
    setError(null);
    setLogs("Система готова. Ожидание данных...");
  };

  return (
    <div className="min-h-screen text-white font-sans selection:bg-blue-500/30 relative overflow-hidden">

      {/* Background LightPillar */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <LightPillar
          topColor="#3300ff"
          bottomColor="#0065ff"
          intensity={1.2}
          rotationSpeed={0.9}
          glowAmount={0.002}
          pillarWidth={4.8}
          pillarHeight={0.5}
          noiseIntensity={0.3}
          pillarRotation={90}
          interactive={false}
          mixBlendMode="screen"
          quality="high"
        />
      </div>

      <div className="relative z-10 min-h-screen">
          <header className="flex justify-between items-center p-6 border-b border-gray-800/50 bg-black/40 backdrop-blur-md">
            <div className="flex items-center space-x-3">
              <MapPin className="text-blue-500" />
              <h1 className="text-xl font-bold tracking-wider drop-shadow-md">
                GEOLOCATOR <span className="text-blue-500">v3.0</span>
              </h1>
            </div>
            <PillNav
              items={["Карта", "Анализ", "Настройки"]}
              activeItem={activeTab}
              onChange={setActiveTab}
            />
          </header>

          <main className="max-w-6xl mx-auto p-6 mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">

            {/* Left Column: Input Panel */}
            <div className="lg:col-span-1 space-y-6">
              <FluidGlass className="p-6 rounded-2xl shadow-2xl relative overflow-hidden" highlightColor="rgba(59, 130, 246, 0.2)">

                  <h2 className="text-lg font-semibold mb-4 flex items-center relative z-10"><Camera className="mr-2 w-5 h-5 text-gray-400" /> Источник данных</h2>

                  <label className="relative z-10 border-2 border-dashed border-gray-600 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 hover:bg-blue-900/20 transition-all bg-black/40">
                    <Upload className="w-8 h-8 text-gray-400 mb-2" />
                    <span className="text-sm text-gray-300 text-center break-all">{file ? file.name : "Загрузить изображение"}</span>
                    <input type="file" className="hidden" onChange={(e) => setFile(e.target.files[0])} accept="image/*" />
                  </label>

                  <div className="mt-6 space-y-4 relative z-10">
                    <div>
                      <label className="text-xs text-gray-400 uppercase font-semibold mb-1 block">Пропорция тени (Высота/Длина)</label>
                      <input
                        type="number" step="0.1"
                        value={shadowRatio} onChange={e => setShadowRatio(e.target.value)}
                        className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-sm focus:border-blue-500 outline-none text-white placeholder-gray-600"
                        placeholder="напр. 1.5"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 uppercase font-semibold mb-1 block">Время съемки (YYYY-MM-DD...)</label>
                      <input
                        type="text"
                        value={timestamp} onChange={e => setTimestamp(e.target.value)}
                        className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-sm focus:border-blue-500 outline-none text-white placeholder-gray-600"
                        placeholder="2023-05-12T12:00:00Z"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-gray-400 uppercase font-semibold mb-1 block">Примерная долгота (опционально)</label>
                      <input
                        type="number" step="0.000001"
                        value={longitude} onChange={e => setLongitude(e.target.value)}
                        className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-sm focus:border-blue-500 outline-none text-white placeholder-gray-600"
                        placeholder="напр. 37.6173"
                      />
                    </div>
                  </div>

                  <div className="mt-8 flex justify-center relative z-10 w-full">
                    <ClickSpark>
                      <button
                        onClick={handleAnalyze}
                        disabled={!file || loading}
                        className="relative overflow-hidden group w-full bg-blue-600/80 hover:bg-blue-500/90 text-white font-semibold py-3 px-8 rounded-xl shadow-[0_0_20px_rgba(37,99,235,0.6)] transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-blue-400/50 backdrop-blur-lg"
                      >
                         <span className="relative z-10">{loading ? "Анализ..." : "Начать анализ"}</span>
                      </button>
                    </ClickSpark>
                  </div>
              </FluidGlass>

              <FluidGlass className="p-4 rounded-xl font-mono text-xs overflow-hidden h-40 shadow-lg" highlightColor="rgba(255, 255, 255, 0.05)">
                <h3 className="text-gray-400 mb-2 flex items-center"><Activity className="w-3 h-3 mr-2 text-blue-400" /> Журнал работы</h3>
                <div className="text-gray-300">
                    <TextType text={logs} speed={30} />
                </div>
              </FluidGlass>
            </div>

            {/* Right Column: Results Display */}
            <div className="lg:col-span-2 space-y-6">

              {loading && (
                <FluidGlass className="flex flex-col items-center justify-center h-64 rounded-2xl" highlightColor="rgba(59, 130, 246, 0.2)">
                  <OrbitImages images={["Y", "2G", "G", "OSM"]} />
                  <p className="mt-8 text-blue-300 font-mono text-sm animate-pulse">Перекрестная проверка баз данных...</p>
                </FluidGlass>
              )}

              {!loading && !results && !error && (
                <FluidGlass className="flex items-center justify-center h-64 rounded-2xl border-dashed border-gray-600/50" highlightColor="rgba(255, 255, 255, 0.05)">
                  <p className="text-gray-400 text-sm">Загрузите изображение для получения OSINT-данных.</p>
                </FluidGlass>
              )}

              {!loading && error && (
                <FluidGlass className="flex flex-col items-center justify-center p-8 rounded-2xl border-red-500/50" highlightColor="rgba(239, 68, 68, 0.2)">
                  <AlertCircle className="w-12 h-12 text-red-500 mb-4 drop-shadow-md" />
                  <h3 className="text-xl font-semibold text-red-400 mb-2">Сбой анализа</h3>
                  <p className="text-red-200/90 mb-6 text-center">{error}</p>
                  <button
                    onClick={handleReset}
                    className="flex items-center bg-red-600/30 hover:bg-red-600/50 text-white font-semibold py-2 px-6 rounded-lg transition-colors border border-red-500/40 shadow-lg"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Попробовать снова
                  </button>
                </FluidGlass>
              )}

              {!loading && results && !error && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

                  {/* Messages from Backend */}
                  {results.messages && results.messages.length > 0 && (
                    <div className="bg-yellow-500/20 border border-yellow-500/40 p-4 rounded-xl text-yellow-100 text-sm backdrop-blur-md shadow-lg">
                      {results.messages.map((msg, i) => <p key={i}>{msg}</p>)}
                    </div>
                  )}

                  {/* Coordinates Result */}
                  <FluidGlass className="p-8 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between" highlightColor="rgba(59, 130, 246, 0.3)">
                    <div className="relative z-10">
                      <h2 className="text-sm text-gray-300 uppercase tracking-widest mb-2 font-medium">Результат хронолокации</h2>
                      <div className="text-4xl sm:text-5xl font-light text-blue-300 drop-shadow-lg tracking-tight">
                        {results.chronolocation ? (
                          <DecryptedText text={`LAT: ${results.chronolocation.estimated_latitude.toFixed(4)}`} duration={1500} />
                        ) : (
                          <FuzzyText>Недостаточно данных для координат</FuzzyText>
                        )}
                      </div>
                    </div>
                    {results.chronolocation && (
                      <div className="mt-4 sm:mt-0 relative z-10 bg-blue-500/30 border border-blue-400/50 px-4 py-2 rounded-xl text-sm text-blue-50 shadow-[0_0_15px_rgba(59,130,246,0.5)] backdrop-blur-md font-medium">
                        Уверенность: Высокая (Теневой анализ)
                      </div>
                    )}
                  </FluidGlass>

                  {/* Grid Data */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <FluidGlass className="p-6 rounded-2xl" highlightColor="rgba(255, 255, 255, 0.1)">
                      <h3 className="text-gray-300 text-sm font-semibold mb-4 tracking-wide">Извлеченный текст (OCR)</h3>
                      <p className="text-gray-100 font-mono text-sm leading-relaxed">
                        {results.ocr_text || <span className="text-gray-500 italic">Текст не обнаружен</span>}
                      </p>
                      {results.ocr_text && (
                        <div className="absolute top-4 right-4 opacity-80">
                          <StickerPeel><span className="text-[10px] leading-tight font-bold text-center">CYRILLIC<br/>DETECTED</span></StickerPeel>
                        </div>
                      )}
                    </FluidGlass>

                    <FluidGlass className="p-6 rounded-2xl" highlightColor="rgba(255, 255, 255, 0.1)">
                      <h3 className="text-gray-300 text-sm font-semibold mb-4 tracking-wide">Обнаруженные объекты</h3>
                      <ul className="space-y-3 text-sm text-gray-200">
                        {Object.entries(results.detections).map(([key, val]) => (
                          val && val.length > 0 && (
                            <li key={key} className="flex justify-between border-b border-gray-800/50 pb-2">
                              <span className="capitalize text-gray-300">{key.replace('_', ' ')}</span>
                              <span className="text-blue-300 font-mono font-medium">{val.length}</span>
                            </li>
                          )
                        ))}
                        {Object.values(results.detections).every(v => !v || v.length === 0) && (
                          <li className="text-gray-500 italic">Значимые объекты не обнаружены</li>
                        )}
                      </ul>
                    </FluidGlass>
                  </div>

                  {/* Climate Data */}
                  {results.weather_data && (
                    <FluidGlass className="p-6 rounded-2xl" highlightColor="rgba(255, 255, 255, 0.1)">
                       <h3 className="text-gray-300 text-sm font-semibold mb-4 tracking-wide">Историческая сводка погоды</h3>
                       <div className="grid grid-cols-3 gap-4 text-sm">
                          <div className="bg-black/40 border border-gray-800/50 p-4 rounded-xl text-center shadow-inner">
                            <div className="text-gray-400 mb-1 text-xs uppercase tracking-wider">Температура</div>
                            <div className="text-xl font-light text-white">{results.weather_data.temperature ?? '?'}°C</div>
                          </div>
                          <div className="bg-black/40 border border-gray-800/50 p-4 rounded-xl text-center shadow-inner">
                            <div className="text-gray-400 mb-1 text-xs uppercase tracking-wider">Осадки</div>
                            <div className="text-xl font-light text-blue-200">{results.weather_data.precipitation ?? '?'}мм</div>
                          </div>
                          <div className="bg-black/40 border border-gray-800/50 p-4 rounded-xl text-center shadow-inner">
                            <div className="text-gray-400 mb-1 text-xs uppercase tracking-wider">Снег</div>
                            <div className="text-xl font-light text-gray-100">{results.weather_data.snowfall ?? '?'}см</div>
                          </div>
                       </div>
                    </FluidGlass>
                  )}

                  {/* Deep Links */}
                  {results.links && (
                    <FluidGlass className="p-6 rounded-2xl" highlightColor="rgba(59, 130, 246, 0.15)">
                      <h3 className="text-gray-300 text-sm font-semibold mb-4 flex items-center tracking-wide"><Map className="mr-2 w-4 h-4 text-blue-400" /> Прямые ссылки на геосервисы</h3>
                      <div className="flex flex-wrap gap-3">
                        {Object.entries(results.links).map(([provider, url]) => (
                          <a
                            key={provider}
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-center px-4 py-2.5 bg-blue-900/20 hover:bg-blue-800/40 border border-blue-500/30 rounded-xl text-sm text-blue-200 transition-all shadow-md hover:shadow-[0_0_15px_rgba(59,130,246,0.3)]"
                          >
                            <LinkIcon className="w-3 h-3 mr-2 opacity-70" />
                            {provider}
                          </a>
                        ))}
                      </div>
                    </FluidGlass>
                  )}

                </div>
              )}
            </div>
          </main>
      </div>
    </div>
  );
}
