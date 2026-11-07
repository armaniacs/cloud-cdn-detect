# DNSリゾルバ依存の名前解決 — 調査 + スキル改訂デザイン (2026-11-07)

## 背景と目的

`cloud-cdn-detect` の DNS 手順 (`SKILL.md §3`) は `dig +short <host>` のみで、
どのリゾルバに聞いたかが記録に残らない。AWS では解決場所 (VPC内/外、
どのパブリックリゾルバか) により答えが変わるため、観測の再現性と
推論の信頼性が落ちる。本デザインは文献調査 (B) と手元のパブリック実測で
裏付けを取り、スキル改訂 (A) に反映する。VPC内実測・VPC Lattice・
Route 53 Global Resolver の実測は GitHub issue で協力者を募集する。

- 方針: C (調査 + スキル改良の両方)
- 検証範囲: B (文献どまり。VPC実機検証は issue 募集)
- 必須スコープ: (1) VPC内DNS基礎、(2) パブリックDNS組み合わせ、(4) スキル運用ルール
- 別issue: (3) VPC Lattice、Route 53 Global Resolver (2026-03 GA、高額のため単独検証困難)
- アプローチ: 案2 (文献 + パブリック実測ハイブリッド)
- 完成形: C (調査レポート + スキル改訂案 + issue雛形2件)

## セクション1: 調査設計

### 文献ソース優先順位

1. AWS公式Docs (VPC User Guide DNS章、Route 53 Developer Guide、Resolver / DNS Firewall章)
2. AWS公式ブログ / What's New (Global Resolver GA 2026-03 等、日付付きで記録)
3. 公開記事 (Zenn / Qiita / エンジニアブログ)。再現コマンドがあるものを優先し、
   推測記事は一次情報と区別する。

### 実測マトリクス (手元実施分)

- 対象: `example.com` 等の無害なドメインと、過去観測のCDN系公開ドメイン (数回のみ、低頻度)。
- コマンド形: `dig +short <host> @<resolver>` を基本とし、必要に応じ `+dnssec` 等で補足。
  resolver = system-default / `1.1.1.1` / `8.8.8.8` / `9.9.9.9` で突き合わせる。
- 記録項目: 使用リゾルバ、実行時刻、応答IP、CNAME有無、TTL、EDNS/ECSの有無。
  食い違いは「場所で答えが変わる実例」としてレポートに残す。
- 実施済み前提: 現行環境の system-default は `172.20.10.1` (+ link-local IPv6)。
  `scutil --dns` で確認済み (2026-11-07)。
- やらないこと: VPC内実測、Lattice実測、Global Resolver実測、高頻度連打。

### 調査観点

- (1) VPCリゾルバ (`169.254.169.253` / `VPC CIDR+2`)、プライベートホストゾーン、
  Resolver Endpoint、DNS Firewall が外からの dig と何を変えるか。
- (2) パブリックリゾルバ間の差 (キャッシュ、ECS、フィルタ) と、
  リゾルバ非明示の dig が何を見落とすか。
- (4) スキルへの落とし込み要件 (リゾルバ記録義務化、複数リゾルバ突き合わせ、VPC内注意書き)。

## セクション2: スキル改訂設計

### SKILL.md §3 改訂案

- `dig +short <host>` を `dig +short <host> @<resolver>` 形に変え、使用リゾルバの記録を必須化。
  デフォルト1行 + `@1.1.1.1` / `@8.8.8.8` 突き合わせを推奨手順にする。
- 冒頭に「自分のリゾルバ確認」ステップ追加
  (`scutil --dns` / `/etc/resolv.conf` / `systemd-resolve --status` のいずれか)。
- Pitfalls 追記: 「Route 53エイリアスはCNAMEに出ない」「VPC内プライベートゾーンは
  外から見えない」「Lattice名は関連付けVPCからのみ解決」。
- 報告雛形の Evidence 表に `Resolver` 列を追加。

### provider-signatures.md の扱い

- 今回は署名追加ではなく AWS 章に「解決場所による見え方の違い」注記を足す程度。
  新署名が出た場合の現行ルール (web検索で一次情報確認後に追記、観測対象名は記録しない) は維持。
- VPC内・Lattice・Global Resolver の署名化は issue 側の検証待ちとし、未確認情報は書かない。

## セクション3: 成果物構成と issue 雛形

### 成果物3点

1. 調査レポート (`docs/research/2026-11-07-dns-resolution.md`):
   文献まとめ + 手元実測マトリクス + 内外の可視境界整理。
2. 本design doc (`docs/superpowers/specs/2026-11-07-dns-resolver-design.md`): 確定版。コミット対象。
3. 協力者募集 issue 雛形2件:
   - `issue-lattice.md`: VPC Lattice 検証 (関連付けVPCからの dig、私有DNS相互作用、再現手順と期待結果の空欄付き)。
   - `issue-global-resolver.md`: Route 53 Global Resolver (2026-03 GA発表リンク、費用注意、検証手順の叩き台)。

### 成功基準

- レポートの全表に「どのリゾルバで何を見たか」が明記されている。
- design doc にプレースホルダ・矛盾がない。
- 雛形2件がそのまま GitHub に貼れる状態になっている。

## スコープ外 (明示)

- VPC内・Lattice・Global Resolver の実機検証。
- ポートスキャン等の active probing (スキル ground rules の禁止事項は維持)。
- 署名DBへの未確認署名の追加、第三者ターゲット名の記録。
