# Day 9 B - 3 公安类专业跳过 (flag: irreducible-api-filter)

跳过原因: 触发 MiniMax M3 API content filter (error 1027 output_new_sensitive).

| slug | 中文 | code | 跳过原因 |
|------|------|------|---------|
| coast-guard-vessel-command | 海警舰艇指挥与技术 | 083110 | 公安海警学院唯一开设, 武警敏感词触发 |
| counterterrorism-policing | 反恐警务 | 030621 | "反恐" 触发 content filter |
| judicial-police-studies | 司法警察学 | 030106 | 监所司法警察敏感 |

待重启 LLM provider (DeepSeek/Moonshot) 之后再做.
