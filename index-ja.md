---
layout: default
lang: ja
title: cloud-cdn-detect（日本語）
---

[English](./) | **日本語**

# cloud-cdn-detect

WebサイトやAPIの背後で動くクラウド・CDN・ホスティング事業者を、
受動的な外部観測だけで推定するスキルです。観測事実と推論を分離し、
証拠表と確度つきで報告します。

```bash
npx skills add armaniacs/cloud-cdn-detect
```

## ドキュメント

- [スキルの手順 (SKILL.md)](./SKILL.html) ※英語
- [事業者シグネチャ表](./references/provider-signatures.html) ※英語
- [変更履歴](./CHANGELOG.html) ※英語
- [コントリビュート手順（日本語）](./CONTRIBUTING-ja.html)

## 報告形式

```markdown
## Conclusion
Edge: <CDN/WAF> / Platform: <PaaS or n/a> / Origin: <IaaS/ホスティング or unknown>
(score S_total, confidence: high/medium/low)
```

受動観測のみ: 通常の`curl`、`dig`、`whois`、TLS確認、公式IPレンジ、
公開Web情報だけを使います。ポートスキャンやオンデマンドスキャンは行いません。
