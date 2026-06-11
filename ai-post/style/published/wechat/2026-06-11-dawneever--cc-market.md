

# takeover v2 鎶€鏈媶瑙ｏ細浠?Bash heredoc 鍒?MCP 鏈嶅姟鍣紝涓€涓妯″瀷璋冨害鎻掍欢鐨勬灦鏋勫崌绾?鍓嶆鏃堕棿鎴戝彂甯冧簡涓€绡囨帹鏂囪鎴?vibe coding 浜嗕竴涓?claude code 鎻掍欢鍙?Takeover 銆?
鍦╲1 閭ｇ増閲岋紝鎴戝疄鐜颁簡"鍦?Claude Code 閲屽悓鏃朵娇鍞や笁涓?AI 鎵撳伐"銆?杩欏凡缁忔槸鎴戞棩甯哥敤寰楁渶鍕ょ殑鎻掍欢浜嗏€斺€擟laude 鍋氭柟妗堬紝DeepSeek 鎾镐唬鐮侊紝Codex 閿愯瘎銆?浣嗘渶杩?Claude Code 鏇存柊浜?Workflow 鍔熻兘锛屾垜鍏村鍦版妸鎵€鏈?skill 鍜屾彃浠跺線 workflow 涓婅縼绉伙紝Takeover 鍗′綇浜嗐€?
Workflow agent 娌℃湁 Bash 鏉冮檺銆傝€?Takeover v1 鐨勬暣涓ā鍨嬫淳鍙戦摼璺紝灏卞缓鍦?Bash heredoc 涓娿€?
杩欎笉鏄姞涓?if-else 鑳界粫杩囧幓鐨勯棶棰樸€傝皟搴﹀眰鐨勫叆鍙ｄ笉瀵癸紝寰楅噸鍐欍€?
涓嬮潰鎷?v2 鐨勫洓涓牳蹇冩灦鏋勫喅绛栤€斺€旀瘡涓€涓儗鍚庨兘鏈変竴涓叿浣撶殑銆佹妸鎴戦€煎埌闈炴敼涓嶅彲鐨勬椂鍒汇€?


## 鍐崇瓥涓€锛欱ash heredoc 鈫?MCP stdio 鏈嶅姟鍣?
v1 鐨勬祦绋嬫槸杩欐牱鈥斺€旂敤鎴锋暡 `/takeover:continue --provider deepseek "review this PR"`锛宼akeover agent 鎶婁笂涓嬫枃鎵撳寘锛岀劧鍚庢墽琛岋細

```bash
node companion.mjs <<'PROMPT'
<鐢ㄦ埛浠诲姟鍜屼笂涓嬫枃>
PROMPT
```

鍗曞紩鍙?heredoc 涓嶅仛鍙橀噺灞曞紑锛屽ぉ鐒堕槻 shell 娉ㄥ叆鈥斺€旇繖鏄垜褰撴椂鐗规剰閫?Bash 璺緞鐨勭悊鐢便€備絾闂涔熷緢鑷村懡锛氳繖琛屽懡浠ゅ彧鏈?Bash tool 鑳借窇銆俉orkflow agent 涓嶈銆?
Claude Code 鐨?Workflow 鍑烘潵涔嬪悗锛屾垜绗竴鏃堕棿鎯虫妸 sharp-review 鐨?Codex 瀹￠槄鑰呮斁杩涘浐鍖栫殑宸ヤ綔娴侀噷鈥斺€旇窇涓嶉€氥€俉orkflow agent 璋冧笉浜?Bash锛孋odex 瀹￠槄鑰呮案杩滃惎鍔ㄤ笉浜嗐€?
鎴戦€変簡 MCP stdio銆備笉鏄洜涓哄畠鏂帮紝鏄洜涓哄畠涓嶉渶瑕佸Ε鍗忋€侶TTP server 瑕佸鐞嗙鍙ｅ拰闃茬伀澧欙紝缁х画鐢?Bash 鍔?Workflow 缁曡矾鏄墦琛ヤ竵銆侸SON-RPC over stdin/stdout 鏄?Claude Code 鐨勫師鐢熸彃浠跺崗璁€斺€旈浂缃戠粶寮€閿€锛宲rompt 鍙傛暟鐩存帴璧?JSON params锛宻hell 娉ㄥ叆鍦ㄦ灦鏋勫眰闈㈡秷澶变簡銆?
浠ｄ环鏄粠 96 琛岄噸鍐欏埌绾?300 琛屻€傛崲鏉ヤ簡涓変釜 MCP tool 鍜屼换浣?MCP 娑堣垂鑰呴兘鑳界洿鎺ヨ皟鐢ㄧ殑鍏ュ彛锛?
```javascript
// mcp-server.mjs 鈥?JSON-RPC 2.0 over stdin/stdout, ~300 lines
export const TOOLS = [
  { name: "call_model",   /* 浜斾釜 dispatch mode */ },
  { name: "list_models",  /* 鍝簺 provider 鍙敤 */ },
  { name: "codex_status", /* Codex 瑁呬簡娌°€佺櫥浜嗘病 */ },
];

async function main() {
  const rl = createInterface({ input: process.stdin });
  for await (const line of rl) {
    const { id, method, params } = JSON.parse(line);
    switch (method) {
      case "initialize": send({ jsonrpc: "2.0", id, result: { capabilities: { tools: {} } } }); break;
      case "tools/list": send({ jsonrpc: "2.0", id, result: { tools: TOOLS } }); break;
      case "tools/call": /* 鈫?handleToolCall(params.name, params.arguments) */; break;
    }
  }
}
```

## 鍐崇瓥浜岋細鐩磋繛 Codex app-server锛岀爫鎺夌涓夋柟鎻掍欢渚濊禆

v1 閲岋紝璁?takeover 璋?Codex 杩欎釜鎿嶄綔璁╂垜寰堜笉鐖解€斺€旇鍏堣绗笁鏂规彃浠讹細`openai/codex-plugin-cc` 鎵嶈兘鍐?claude code 涓皟鐢?codex 瀹℃煡浠ｇ爜锛?鍙﹀锛屾渶杩戝惉璇?codex 鍙互鐩存帴璋冪敤 gpt-image2 鐢熸垚鍥剧墖锛岀洰鍓嶄富娴佸仛娉曟槸瑕佸啀瑁呬竴涓?`codex-image@codex-image-in-cc` 鎵嶈兘鍐?claude code 涓皟鐢ㄣ€?v1 鐗堟湰閲岋紝涓轰簡璋冪敤 codex `companion.mjs` 閲屾湁涓?`findCodexCompanion()` 鍑芥暟锛屽仛鐨勪簨灏辨槸鎽歌繘鍒殑鎻掍欢鐨勭洰褰曟壘鍏ュ彛鏂囦欢銆倀akeover 鍚嶄箟涓婃槸涓ā鍨嬭皟搴︿腑闂村眰锛屼絾瀹為檯涓婂畠瀵瑰簳灞?provider 鐨勬娊璞℃槸婕忕殑鈥斺€旂敤鎴峰緱鑷繁绠℃彃浠朵箣闂寸殑渚濊禆鍏崇郴锛岃浜嗚繖涓繕寰楄閭ｄ釜锛屽己杩棁寰堥毦鍙椼€?
v2 鎴戞妸杩欎釜渚濊禆閾惧交搴曠爫浜嗐€俙CodexAppServerClient` 绫荤洿鎺?spawn `codex app-server`锛岃蛋 JSON-RPC 2.0鈥斺€旀彙鎵嬨€侀€氱煡璺敱銆佺敓鍛藉懆鏈熺鐞嗭紝鍏ㄥ湪涓€涓被閲岋細

```javascript
// scripts/codex/app-server.mjs 鈥?direct codex app-server JSON-RPC client
// 绀烘剰浠ｇ爜锛宻end/onNotification/stop 鏂规硶涓虹鍚嶇缉鍐?export class CodexAppServerClient {
  async start() {
    const bin = this.codexPath || findCodexBinary();
    this.child = spawn(bin, ["app-server"], {
      stdio: ["pipe", "pipe", "pipe"],
      shell: process.platform === "win32",
    });
    const initResult = await this.send("initialize", {
      protocolVersion: "1.0",
      clientInfo: { name: "takeover", version: "2.3.5" },
    });
    return initResult;
  }

  send(method, params) { /* Promise锛宊handleLine() 鏀跺埌 JSON-RPC response 鏃?resolve */ }

  onNotification(method, handler) { /* 璺敱 turn/completed, item/completed 绛夐€氱煡 */ }

  async stop() { /* send shutdown 鈫?kill process */ }
}
```

璁捐涓婃垜鏁呮剰淇濇寔绠€鍗曪細涓€涓姹備竴涓繘绋嬶紝娌℃湁 broker锛屾病鏈夊父椹?daemon銆傜敤瀹屽氨鍏筹紝骞插噣鍒╄惤銆?
鍥剧墖鐢熸垚鍜岀紪杈戜篃椤哄娍鎺ヤ笂浜嗏€斺€擿codex exec --full-auto` 璋?Codex 鍐呯疆鐨?imagegen skill 璧?CLI 瀛愯繘绋嬶紝灏侀潰鍥俱€佹灦鏋勫浘銆佺紪杈戠幇鏈夊浘鐗囧叏鎼炲畾锛屼笉澧炲姞浠讳綍澶栭儴渚濊禆銆傦紙娉ㄦ剰锛氬浘鐗囪矾寰勮蛋鐨勬槸 `codex exec` CLI锛屼笉鏄?JSON-RPC CodexAppServerClient鈥斺€斾袱涓笉鍚屼唬鐮佽矾寰勩€傦級

杩欎釜 `CodexAppServerClient` 绫绘垜鐗规剰璺?takeover 鐨勪笟鍔￠€昏緫瑙ｈ€︿簡鈥斺€斾互鍚庡叾浠栨彃浠舵兂璺?`codex app-server` 瀵硅瘽锛屽彲浠ョ洿鎺?import 杩欎釜绫汇€?
## 鍐崇瓥涓夛細浜旀潯 dispatch 鍒嗗弶 + 纭畾鎬?flag 瑙ｆ瀽

v1 鍙湁涓€鏉¤矾鈥斺€旀妸浠诲姟鎵旂粰鎸囧畾妯″瀷锛岀瓑缁撴灉鍥炴潵銆備絾鐢ㄤ簡鍑犲懆涔嬪悗鍙戠幇闇€瑕佺殑涓嶆杩欎竴鏉°€傛湁鐨勪换鍔¤璺戝畬鏁寸殑 agent loop锛屾湁鐨勮瀵规姉鎬у鏌ワ紝鏈夌殑瑕佺敓鎴愬浘鐗団€斺€斿け璐ユā寮忎笉涓€鏍凤紝灏变笉璇ヨ蛋鍚屼竴鏉¤矾銆?
v2 鐨?`handleCallModel()` 閲岄暱鍑轰簡浜旀潯鍒嗗弶锛?
```javascript
// mcp-server.mjs 鈥?five dispatch modes, provider-aware routing
// 绀烘剰浠ｇ爜锛岀渷鐣ヤ簡閮ㄥ垎瀹炵幇缁嗚妭
export async function handleCallModel(args) {
  let { provider, model, mode, userPrompt } = args;

  // 纭畾鎬?flag 瑙ｆ瀽 鈥?涓嶇湅 LLM agent 鐨勫垽鏂紝鍙湅 <command> 鍧?  const parsed = parseCommandBlock(userPrompt);
  if (parsed.flags.provider) provider = parsed.flags.provider;
  if (parsed.flags.model) model = parsed.flags.model;
  userPrompt = parsed.cleanPrompt;

  const providerConfig = loadProviderConfig(provider);
  const systemPrompt = deriveSystemPrompt(args);

  // Agent mode 鈥?瀹屾暣宸ュ叿璁块棶鏉冮檺
  if (mode === 'agent') return callAgentMode(provider, userPrompt, systemPrompt, model);

  // Guard 鈥?review 鍜?image 妯″紡鍙 codex
  if (mode && mode !== "task" && providerConfig.provider !== "codex")
    throw new Error(`Mode "${mode}" is only supported with --provider codex`);

  // 鎸?provider 鍒嗗彂
  if (providerConfig.provider === "codex") {
    if (mode === "review")         data = await runCodexReview(userPrompt, ...);
    else if (mode === "image-generate") data = await generateImage(userPrompt);
    else if (mode === "image-edit")     data = await editImage(prompt, path);
    else                           data = await callCodexCompanion(userPrompt, ...);
  } else if (providerConfig.native) {
    data = await callNativeClaude(userPrompt, systemPrompt);
  } else {
    data = await callAnthropicAPI(providerConfig, resolvedModel, systemPrompt, userPrompt);
  }

  return { content: [{ type: "text", text: extractText(data) }] };
}
```

涓や釜缁嗚妭鍊煎緱鍗曠嫭璇淬€?
**`<command>` 鍧楃殑纭畾鎬цВ鏋愩€?* v1 渚濊禆 LLM agent 鑷繁鍘昏瘑鍒?`--provider` 鍜?`--model` flag銆傚ぇ澶氭暟鏃跺€欐病闂鈥斺€旂洿鍒版湁涓€娆?agent 鎶?`--provider codex` 瑙ｆ瀽鎴愪簡 `--provider claude`锛孋odex 瀹￠槄娌¤窇鎴愶紝鍗婂皬鏃惰緭鍑虹殑鏄?Claude 鐨勬俯鍜岀偣璇勮€屼笉鏄鎶楁€у鏌ワ紝鐧界瓑浜嗐€傝皟浜嗕竴涓嬪崍鎵嶅畾浣嶅埌杩欎釜 bug銆?
v2 鐨勮В娉曟槸璁?agent 鍙仛瀛楃涓插寘瑁光€斺€旂敤鎴锋暡鐨勫師濮嬪懡浠わ紝鍘熸牱濉炶繘 `<command>` 鏍囩銆俧lag 鐨勮В鏋愭潈浜ょ粰 `parseCommandBlock()`锛?2 琛岃В鏋愬嚱鏁帮細

```javascript
// lib.mjs L149-171 鈥?纭畾鎬?regex锛岃В鏋愯矾寰勪笉缁忚繃 LLM
export function parseCommandBlock(prompt) {
  const re = /^\s*<command>\s*\n?(.*?)\n?\s*<\/command>\s*\n?/s;
  const match = prompt.match(re);
  if (!match) return { flags: {}, cleanPrompt: prompt };

  const cmdText = match[1].trim();
  const flags = {};
  const providerMatch = cmdText.match(/--provider\s+(\S+)/);
  if (providerMatch) flags.provider = providerMatch[1];
  const modelMatch = cmdText.match(/--model\s+(\S+)/);
  if (modelMatch) flags.model = modelMatch[1];
  if (cmdText.match(/--review/))            flags.mode = "review";
  if (cmdText.match(/--image-edit/))        flags.mode = "image-edit";
  else if (cmdText.match(/--image/))        flags.mode = "image-generate";

  return { flags, cleanPrompt: prompt.replace(re, "") };
}
```

姝ｅ垯涓嶄細鎶?`codex` 鐪嬫垚 `claude`銆傚畠娌℃湁"鍒涢€犳€?锛岃€岃繖鎭板ソ鏄В鏋愬懡浠よ flag 鏃堕渶瑕佺殑涓滆タ銆?
**Provider guard銆?* review銆乮mage-generate銆乮mage-edit 涓変釜妯″紡鎴戝姞浜嗙‖ guard鈥斺€斾唬鐮佸眰闈㈠己鍒惰姹?`--provider codex`銆傚鎶楁€у闃呰蛋鐨勬槸 `review/start` JSON-RPC锛屽浘鐗囩敓鎴愯蛋鐨勬槸 `codex exec --full-auto`锛岄兘鏄?Codex 鐙湁鐨勫伐鍏烽摼鑳藉姏銆備綘浼?`--provider deepseek --review`锛岀洿鎺ユ姏 Error锛屼笉鏄?寤鸿涓嶈杩欐牱鍋?銆傝兘鍔涜竟鐣屽氨璇ュ湪浠ｇ爜閲屼綋鐜帮紝涓嶈闈犳枃妗ｈ鏄庛€?
![浜旀潯 dispatch 鍒嗗弶娴佺▼鍥綸(../../images/five-modes-v1.png)

## 鍐崇瓥鍥涳細Agent 妯″紡鈥斺€旂粰 DeepSeek 绌夸笂澶栭楠?
寮曞叆 MCP 涔嬪悗鍑虹幇浜嗕竴涓柊闂銆倂2 鐨?MCP server 璧扮函 JSON-RPC 璋冪敤锛孌eepSeek 鐨?API 鎴戝彧鑳芥嬁鍒颁竴娈垫枃鏈緭鍑衡€斺€斿畠鑳界悊瑙ｄ唬鐮侊紝浣嗕笉鑳借嚜宸?Read 鏂囦欢銆佷笉鑳借窇 Bash銆佹病鏈?agent loop銆倂1 閲?Bash heredoc 铏界劧鍙兘鍦?Skill 閲岃窇锛屼絾瀹冨惎鍔ㄧ殑鏄畬鏁寸殑 Claude Code 鐜锛屾ā鍨嬫湁宸ュ叿銆侻CP 鎹㈡潵浜?Workflow 鍏煎鎬э紝浠ｄ环鏄妸 DeepSeek 鐨勬墜鑴氱爫浜嗐€?
`callAgentMode()` 鏄垜涓撻棬琛ヨ繖涓己鍙ｇ殑鏂规锛?
```javascript
// lib.mjs L51-88 鈥?spawn claude -p 娉ㄥ叆 provider 鐜鍙橀噺锛屽畬鏁村伐鍏疯闂?export async function callAgentMode(provider, userPrompt, systemPrompt, model) {
  const env = loadProviderEnv(provider);
  // 1. 娓呯┖鎵€鏈?ANTHROPIC_* 鐜鍙橀噺
  // 2. 浠?claude_env_settings.json 鍔犺浇 provider 鐨?env block
  // 3. 濡傛灉 model 鏄?tier 鍚?(sonnet/opus/haiku)锛屾槧灏勪负 provider 涓撶敤鍚?
  if (model && provider !== 'claude') {
    const providerConfig = loadProviderConfig(provider);
    env.ANTHROPIC_MODEL = resolveModel(providerConfig, model);
  }

  return new Promise((resolve, reject) => {
    const child = spawn('claude', ['-p', fullPrompt], {
      env,                                    // DeepSeek 鐨?key 鍜?endpoint
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 300000,
      shell: process.platform === 'win32',   // Windows 鍏煎
    });
    // 鏀堕泦 stdout 鈫?杩斿洖缁撴灉
  });
}
```

缈昏瘧鎴愪汉璇濓細鍚姩 Claude Code 鑷繁鐨?agent loop锛坄claude -p`锛夛紝浣嗘妸鐜鍙橀噺鎹㈡垚 DeepSeek 鐨勯厤缃€傛墍浠?agent loop 鐓у父璺戔€斺€擱ead 鏂囦欢銆乄rite 浠ｇ爜銆丅ash 娴嬭瘯鈥斺€斿彧鏄瘡娆?LLM 璋冪敤鍘荤殑涓嶆槸 Anthropic锛屾槸 DeepSeek銆侰laude Code 鍑哄熀纭€璁炬柦锛孌eepSeek 鍑鸿剳瀛愩€傜瓑浜庣粰瀹冪┛浜嗕欢澶栭楠笺€?
涓や釜閰嶅缁嗚妭鏄垜韪╀簡鍧戞墠鍔犱笂鐨勩€俙loadProviderEnv()` 鍔犺浇鍓嶅厛鎶婃墍鏈?`ANTHROPIC_*` 寮€澶寸殑鐜鍙橀噺鍒犲共鍑€锛屽啀娉ㄥ叆 provider 鐨勯厤缃€傜涓€鐗堟病鍋氭竻鐞嗭紝鏈満鐨?Claude API key 鐩存帴閫忎紶杩涗簡 DeepSeek 璋冪敤銆俙resolveModel()` 鍋?tier 鍚嶆槧灏勨€斺€旂敤鎴峰啓 `--model sonnet`锛屼絾 DeepSeek 鍙 `deepseek-v4-flash`銆傜涓€娆″繕浜嗘槧灏勶紝model not found銆?
杩樻湁涓€涓杩界潃鎶ヤ簡涓夋 bug 鎵嶈ˉ涓婄殑锛氬ぇ閮ㄥ垎 `spawn()` 璋冪敤閮藉甫浜?`shell: process.platform === "win32"`銆俉indows 涓?`spawn('claude')` 涓嶈閬撶悊鍦板幓瑙ｆ瀽 POSIX shell 鑴氭湰鑰屼笉鏄皟 `claude.cmd`銆俿harp-review 鐨?Codex reviewer 鍦?Windows 涓婂洜涓鸿繖涓寕浜嗭紝鍗′簡涓€涓笅鍗堛€?


## 鏀跺熬

鍥炲ご鐪嬭繖鍥涗釜鍐崇瓥鈥斺€攈eredoc 鎹?MCP銆佺洿杩?Codex 鐮嶇涓夋柟渚濊禆銆佷簲鏉?dispatch 鍔犵‘瀹氭€цВ鏋愩€佺粰 DeepSeek 绌夸笂澶栭楠尖€斺€旀湁涓€涓叡鍚岀殑閫昏緫锛?*v1 璇佹槑浜嗚繖浠朵簨鏈変环鍊硷紝v2 鎶婃瘡涓崱鐐逛慨鍒版灦鏋勫眰闈紝鑰屼笉鏄湪琛ㄩ潰璐磋兌甯︺€?*

shell 娉ㄥ叆涓嶆槸鍦?heredoc 涓婂姞寮曞彿淇ソ鐨勶紝鏄妸 shell 鏁翠釜鍒犳帀淇ソ鐨勩€侰odex 渚濊禆涓嶆槸鍔犱釜 fallback 璺緞瑙ｅ喅鐨勶紝鏄洿鎺ヨ窡 app-server 璇磋瘽瑙ｅ喅鐨勩€俧lag 瑙ｆ瀽涓嶆槸缁?LLM 鍔犳洿澶氭彁绀鸿瘝淇殑锛屾槸鐢ㄦ鍒欎唬鏇?LLM 瑙ｆ瀽淇殑銆侱eepSeek 娌℃湁宸ュ叿鑳藉姏涓嶆槸"閭ｅ氨涓嶇敤宸ュ叿"缁曡繃鍘荤殑锛屾槸鍊?Claude Code 鐨?agent loop 缁欏畠绌夸笂澶栭楠艰В鍐崇殑銆?
浠ｇ爜鍦?GitHub锛岄浂 npm 渚濊禆锛岀函 Node.js ESM銆?
GitHub: https://github.com/DawnEver/cc-market

鎴栬€呯洿鎺ュ湪 Claude Code 閲岋細

```
/plugin marketplace add DawnEver/cc-market
/plugin install takeover@cc-market
```

