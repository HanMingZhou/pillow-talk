// 应用状态
let stream = null;
let conversationId = null;
let availableVoices = [];
let isPaused = false;
let pendingSentences = [];
let isPlaying = false;
let isCameraActive = false;
let apiUrl = '';

// DOM 元素
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const cameraOverlay = document.getElementById('cameraOverlay');
const cameraBtn = document.getElementById('cameraBtn');
const pauseAudioBtn = document.getElementById('pauseAudioBtn');
const clearChatBtn = document.getElementById('clearChatBtn');
const settingsBtn = document.getElementById('settingsBtn');
const sendMessageBtn = document.getElementById('sendMessageBtn');
const userInput = document.getElementById('userInput');
const chatMessages = document.getElementById('chatMessages');
const statusBar = document.getElementById('statusBar');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');
const closeSidebarBtn = document.getElementById('closeSidebarBtn');
const providerSelect = document.getElementById('provider');
const systemPromptInput = document.getElementById('systemPrompt');
const enableTTSCheckbox = document.getElementById('enableTTS');
const promptTemplateSelect = document.getElementById('promptTemplate');
const voiceSelect = document.getElementById('voiceSelect');
const speechRateInput = document.getElementById('speechRate');
const rateValueSpan = document.getElementById('rateValue');
const customModelSettings = document.getElementById('customModelSettings');
const modelNameInput = document.getElementById('modelNameInput');
const apiKeyInput = document.getElementById('apiKeyInput');
const baseUrlInput = document.getElementById('baseUrlInput');

// Prompt 模板
const promptTemplates = {
    custom: '你是一个友好的助手',
    museum: '你是一位博学多才的博物馆讲解员，擅长用生动有趣的方式介绍各种物品的历史、文化背景和有趣故事。请用温和、专业且富有感染力的语气回答。',
    pet: '你是一只可爱的小宠物，用天真活泼的语气和主人交流。你会用简单有趣的方式描述看到的东西，偶尔撒撒娇。',
    scientist: '你是一位严谨的科普专家，擅长用通俗易懂的语言解释科学原理和知识。请用准确、清晰且富有启发性的方式回答。',
    critic: '你是一位毒舌评论家，用幽默讽刺的方式点评眼前的事物。你的评论犀利但不失风趣，能够一针见血地指出事物的特点。',
    companion: '你是一个"人间夸夸机·顶级情绪价值供应商"。无论用户给你看见的是什么，你都必须从"发现美好"的视角出发，进行高度赞美与诗意升华。'
};

// 初始化
async function init() {
    try {
        apiUrl = await window.electronAPI.getBackendUrl();
        showStatus('正在连接后端...', 'info');
        
        const isHealthy = await checkBackend();
        if (isHealthy) {
            showStatus('后端连接成功', 'success');
        } else {
            showStatus('后端连接失败', 'error');
        }
    } catch (error) {
        console.error('初始化失败:', error);
        showStatus('初始化失败: ' + error.message, 'error');
    }
}

// 检查后端连接
async function checkBackend() {
    try {
        const response = await fetch(`${apiUrl}/health`);
        const data = await response.json();
        return data.status === 'healthy';
    } catch (error) {
        return false;
    }
}

// 状态显示
function showStatus(message, type) {
    statusBar.textContent = message;
    statusBar.className = `status-bar ${type}`;
    statusBar.classList.remove('hidden');
    
    setTimeout(() => {
        statusBar.classList.add('hidden');
    }, 3000);
}

function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 语音合成队列管理
function speakText(text) {
    if (!enableTTSCheckbox.checked) return;
    
    let cleanText = text
        .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
        .replace(/[\u{2600}-\u{26FF}]/gu, '')
        .replace(/[\u{2700}-\u{27BF}]/gu, '')
        .replace(/[\u{FE00}-\u{FE0F}]/gu, '')
        .replace(/[\u{1F000}-\u{1F02F}]/gu, '')
        .replace(/[\u{1F0A0}-\u{1F0FF}]/gu, '')
        .replace(/[\u{1F100}-\u{1F64F}]/gu, '')
        .replace(/[\u{1F680}-\u{1F6FF}]/gu, '')
        .replace(/[\u{1F700}-\u{1F77F}]/gu, '')
        .replace(/[\u{1F780}-\u{1F7FF}]/gu, '')
        .replace(/[\u{1F800}-\u{1F8FF}]/gu, '')
        .replace(/[\u{1F900}-\u{1F9FF}]/gu, '')
        .replace(/[\u{1FA00}-\u{1FA6F}]/gu, '')
        .replace(/[\u{1FA70}-\u{1FAFF}]/gu, '')
        .replace(/[✨🌿🛏️🧳🪑🌟🌸💫🎉💖]/g, '');
    
    cleanText = cleanText
        .replace(/[。！？]/g, '，')
        .replace(/[.!?]/g, ',')
        .replace(/["'"'「」『』《》〈〉]/g, '')
        .replace(/[（）()[\]【】]/g, '')
        .replace(/[—…·]/g, ' ')
        .replace(/[：:]/g, '，')
        .replace(/\s+/g, ' ')
        .trim();
    
    if (!cleanText) return;
    
    if (isPaused) {
        pendingSentences.push(cleanText);
        return;
    }
    
    playSentence(cleanText);
}

function playSentence(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    utterance.rate = parseFloat(speechRateInput.value);
    utterance.pitch = 1.0;
    
    const selectedVoice = availableVoices.find(v => v.name === voiceSelect.value);
    if (selectedVoice) {
        utterance.voice = selectedVoice;
    }
    
    utterance.onstart = () => {
        isPlaying = true;
    };
    
    utterance.onend = () => {
        isPlaying = false;
        if (!isPaused && pendingSentences.length > 0) {
            const nextSentence = pendingSentences.shift();
            playSentence(nextSentence);
        }
    };
    
    speechSynthesis.speak(utterance);
}

// 加载语音列表
function loadVoices() {
    availableVoices = speechSynthesis.getVoices();
    const chineseVoices = availableVoices.filter(voice => 
        voice.lang.includes('zh') || voice.lang.includes('CN')
    );
    const voicesToShow = chineseVoices.length > 0 ? chineseVoices : availableVoices;
    
    voiceSelect.innerHTML = '';
    voicesToShow.forEach(voice => {
        const option = document.createElement('option');
        option.value = voice.name;
        option.textContent = `${voice.name} (${voice.lang})`;
        voiceSelect.appendChild(option);
    });
    
    if (voicesToShow.length > 0) {
        voiceSelect.value = voicesToShow[0].name;
    }
}

if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = loadVoices;
}
loadVoices();

// 侧边栏控制
settingsBtn.addEventListener('click', () => {
    sidebar.classList.add('open');
    overlay.classList.add('show');
});

closeSidebarBtn.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
});

overlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
});

// 摄像头控制
cameraBtn.addEventListener('click', async () => {
    if (isCameraActive) {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            video.srcObject = null;
            isCameraActive = false;
            cameraBtn.classList.remove('active');
            cameraOverlay.style.display = 'flex';
            sendMessageBtn.disabled = true;
            showStatus('摄像头已停止', 'info');
        }
    } else {
        try {
            stream = await navigator.mediaDevices.getUserMedia({ 
                video: { width: 1280, height: 720, facingMode: 'user' } 
            });
            video.srcObject = stream;
            isCameraActive = true;
            cameraBtn.classList.add('active');
            cameraOverlay.style.display = 'none';
            sendMessageBtn.disabled = false;
            showStatus('摄像头已启动', 'success');
        } catch (error) {
            showStatus('无法访问摄像头: ' + error.message, 'error');
        }
    }
});

// 捕获当前画面
function captureCurrentFrame() {
    if (!stream) {
        return null;
    }
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    return canvas.toDataURL('image/jpeg', 0.8);
}

// 发送消息
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) {
        showStatus('请输入问题', 'error');
        return;
    }
    
    if (!stream) {
        showStatus('请先启动摄像头', 'error');
        return;
    }
    
    const capturedImageData = captureCurrentFrame();
    if (!capturedImageData) {
        showStatus('无法捕获画面', 'error');
        return;
    }
    
    addMessage(message, 'user');
    userInput.value = '';
    sendMessageBtn.disabled = true;
    showStatus('正在思考...', 'info');
    
    try {
        const requestBody = {
            image_base64: capturedImageData,
            system_prompt: `${systemPromptInput.value}\n\n用户问题: ${message}`,
            provider: providerSelect.value,
            stream: true,
            tts_enabled: false,
            tts_voice: 'default',
            tts_speed: 1.0
        };
        
        if (providerSelect.value === 'custom') {
            const modelName = modelNameInput.value.trim();
            const apiKey = apiKeyInput.value.trim();
            const baseUrl = baseUrlInput.value.trim();
            
            if (!modelName || !apiKey || !baseUrl) {
                showStatus('请填写完整的自定义模型配置', 'error');
                sendMessageBtn.disabled = false;
                return;
            }
            
            requestBody.custom_config = {
                model_name: modelName,
                api_key: apiKey,
                base_url: baseUrl
            };
        }
        
        if (conversationId) {
            requestBody.conversation_id = conversationId;
        }
        
        const response = await fetch(`${apiUrl}/api/v1/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '请求失败');
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let responseText = '';
        let sentenceBuffer = '';
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        chatMessages.appendChild(messageDiv);
        
        const sentenceEnds = ['。', '！', '？', '；', '.', '!', '?', ';', '\n'];
        
        while (true) {
            const {done, value} = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;
                    
                    try {
                        const json = JSON.parse(data);
                        if (json.text) {
                            responseText += json.text;
                            sentenceBuffer += json.text;
                            messageDiv.textContent = responseText;
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                            
                            if (enableTTSCheckbox.checked) {
                                for (const end of sentenceEnds) {
                                    if (sentenceBuffer.includes(end)) {
                                        const sentences = sentenceBuffer.split(end);
                                        for (let i = 0; i < sentences.length - 1; i++) {
                                            if (sentences[i].trim()) {
                                                speakText(sentences[i] + end);
                                            }
                                        }
                                        sentenceBuffer = sentences[sentences.length - 1];
                                        break;
                                    }
                                }
                            }
                        }
                        if (json.conversation_id) {
                            conversationId = json.conversation_id;
                        }
                    } catch (e) {
                        // 忽略解析错误
                    }
                }
            }
        }
        
        if (enableTTSCheckbox.checked && sentenceBuffer.trim()) {
            speakText(sentenceBuffer);
        }
        
        showStatus('回复完成', 'success');
    } catch (error) {
        addMessage('错误: ' + error.message, 'system');
        showStatus('发送失败: ' + error.message, 'error');
    } finally {
        sendMessageBtn.disabled = false;
    }
}

// 清空对话
clearChatBtn.addEventListener('click', () => {
    chatMessages.innerHTML = '';
    conversationId = null;
    addMessage('对话已清空', 'system');
    showStatus('对话已清空', 'info');
});

// 暂停/继续播放
pauseAudioBtn.addEventListener('click', () => {
    if (isPaused) {
        isPaused = false;
        pauseAudioBtn.textContent = '⏸️';
        pauseAudioBtn.title = '暂停播放';
        
        if (pendingSentences.length > 0 && !isPlaying) {
            const nextSentence = pendingSentences.shift();
            playSentence(nextSentence);
        }
        
        showStatus('已继续播放', 'info');
    } else {
        isPaused = true;
        pauseAudioBtn.textContent = '▶️';
        pauseAudioBtn.title = '继续播放';
        
        speechSynthesis.cancel();
        isPlaying = false;
        
        showStatus('已暂停播放', 'info');
    }
});

// 监听 provider 变化
providerSelect.addEventListener('change', (e) => {
    customModelSettings.style.display = e.target.value === 'custom' ? 'block' : 'none';
});

// Prompt 模板切换
promptTemplateSelect.addEventListener('change', (e) => {
    const template = e.target.value;
    if (template !== 'custom') {
        systemPromptInput.value = promptTemplates[template];
        systemPromptInput.disabled = true;
    } else {
        systemPromptInput.disabled = false;
    }
});

// 发送消息
sendMessageBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// 自动调整输入框高度
userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 100) + 'px';
});

// 语速滑块更新
speechRateInput.addEventListener('input', (e) => {
    rateValueSpan.textContent = e.target.value + 'x';
});

// 启动应用
init();
setInterval(checkBackend, 30000);
