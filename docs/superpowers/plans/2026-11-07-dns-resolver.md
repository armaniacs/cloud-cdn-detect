# DNSリゾルバ依存の名前解決 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 文献調査と手元実測でDNS解決場所による見え方の違いを裏付け、cloud-cdn-detectスキルにリゾルバ記録手順を反映し、Lattice/Global Resolver協力者募集issue雛形を作る。

**Architecture:** 文献一次情報と `dig @resolver` 突き合わせ実測を分離して記録し、調査レポートに集約した上で SKILL.md と署名DB注記へ反映する。実機検証できない範囲は再現手順付きissue雛形として切り出す。

**Tech Stack:** `dig`, `scutil --dns`, Markdown, git, GitHub Issues (passive observation only: `dig`, low-volume `curl -sI` のみ)。

---

## File map

- Create: `docs/research/2026-11-07-dns-resolution.md` — 調査レポート本体 (責任: 文献まとめ+実測表+可視境界)。
- Modify: `SKILL.md` — §3 Resolve DNS 改訂 + Pitfalls 追記 + 報告雛形に Resolver 列追加 (責任: 手順の再現性)。
- Modify: `references/provider-signatures.md` — AWS 章に解決場所注記のみ追加 (責任: 誤用防止。署名追加なし)。
- Create: `docs/research/issues/issue-lattice-draft.md` — Lattice 検証募集文面 (責任: 協力者への再現手順)。
- Create: `docs/research/issues/issue-global-resolver-draft.md` — Global Resolver 検証募集文面 (責任: 同上、費用注意付き)。
- Create: `docs/superpowers/plans/2026-11-07-dns-resolver.md` — 本ファイル (責任: 実行手順)。

Spec source: `docs/superpowers/specs/2026-11-07-dns-resolver-design.md`.

---

### Task 1: VPC内DNS基礎の文献調査

**Files:**
- Create: `docs/research/2026-11-07-dns-resolution.md` (Section 1 の雛形まで)
- Test: 目視 + `ls docs/research/`

- [ ] **Step 1: 一次情報を開いて要点を抜き出す**

対象URL (ブラウザまたは `curl -sL` で取得):
- `https://docs.aws.amazon.com/vpc/latest/userguide/vpc-dns.html`
- `https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html`
- `https://docs.aws.amazon.com/route53/latest/developerguide/hosted-zones-private.html`

抜き出す項目 (メモ帳でよい):
- VPCリゾルバの2つの書き方: `169.254.169.253` と `VPC CIDR+2` (例: VPCが `10.0.0.0/16` なら `10.0.0.2`)。
- プライベートホストゾーンは関連付けVPCからのみ解決し、外からの `dig` では見えないこと。
- Resolver Endpoint (Inbound/Outbound) と DNS Firewall がフィルタしうること。

- [ ] **Step 2: レポート雛形を作成する**

```markdown
# DNS解決場所による見え方の違い — 調査レポート (2026-11-07)

## 0. 実行環境のリゾルバ
- system-default: 172.20.10.1 (+ link-local IPv6), `scutil --dns` で確認 (2026-11-07)

## 1. VPC内DNS基礎 (文献)
### VPCリゾルバ
- (Step 1 の要点をここに転記)

### プライベートホストゾーン / Resolver Endpoint / DNS Firewall
- (Step 1 の要点をここに転記)

## 2. パブリックDNS組み合わせ (文献+実測)
- (Task 2-3 で追記)

## 3. 可視境界まとめ
- 外から見える: パブリックゾーン、CNAME/A、エッジIPのwhois/ASN。
- 外から見えない: プライベートゾーン、Lattice名 (関連付けVPCのみ)、オリジン内訳。

## Sources
- (URLと取得日を列挙)
```

保存先: `docs/research/2026-11-07-dns-resolution.md`。

- [ ] **Step 3: 保存を確認してコミットする**

```bash
ls docs/research/2026-11-07-dns-resolution.md
git add docs/research/2026-11-07-dns-resolution.md
git commit -m "docs: scaffold DNS resolution research report"
```
Expected: `ls` がパスを返し、`git log --oneline -1` に上記メッセージが載る。

---

### Task 2: パブリックDNS組み合わせの文献調査

**Files:**
- Modify: `docs/research/2026-11-07-dns-resolution.md` (Section 2 文献パート)
- Test: `grep -n "1.1.1.1" docs/research/2026-11-07-dns-resolution.md`

- [ ] **Step 1: リゾルバ差の観点をメモする**

観点 (そのまま転記して使う):
- キャッシュ差: TTL途中の応答はリゾルバごとに変わりうる。結論にTTLと時刻を添える。
- ECS (EDNS Client Subnet) 差: 位置情報付きGeoDNS回答はリゾルバのECS送出方針で変わりうる。
- フィルタ差: マルウェア/広告ブロック系は応答を変えることがある。`9.9.9.9` 等は用途上フィルタ前提。

- [ ] **Step 2: レポート Section 2 文献パートを追記する**

追記文 (そのまま貼る):
```markdown
## 2. パブリックDNS組み合わせ (文献+実測)
### 文献要点
- `1.1.1.1` (Cloudflare)、`8.8.8.8` (Google)、`9.9.9.9` (Quad9) はキャッシュ・ECS・フィルタ方針が異なるため、CDNのGeo回答は食い違うことがある。
- `dig` でリゾルバを省略すると system-default (本環境では 172.20.10.1) を見ていることになり、再現性が落ちる。`@resolver` 明示が必須。
```

- [ ] **Step 3: 確認してコミットする**

```bash
grep -n "1.1.1.1" docs/research/2026-11-07-dns-resolution.md
git add docs/research/2026-11-07-dns-resolution.md
git commit -m "docs: add public resolver literature notes"
```
Expected: `grep` が1件以上ヒットする (追記文自体に `1.1.1.1` は1件のみ含まれるため)。

---

### Task 3: 手元パブリック実測マトリクス

**Files:**
- Modify: `docs/research/2026-11-07-dns-resolution.md` (Section 2 実測表)
- Test: `grep -n "system-default" docs/research/2026-11-07-dns-resolution.md`

- [ ] **Step 1: 自分のリゾルバを確認する**

```bash
scutil --dns | head -n 12
```
Expected: `nameserver[1] : 172.20.10.1` を含む (環境が変わっていたら実測値をレポートに書く。想定値に固執しない)。

macOS以外の場合はいずれか:
```bash
cat /etc/resolv.conf
```
```bash
systemd-resolve --status | head -n 30
```

- [ ] **Step 2: 4リゾルバで突き合わせる (低頻度、各1-2回のみ)**

```bash
for r in 172.20.10.1 1.1.1.1 8.8.8.8 9.9.9.9; do echo "== @${r} =="; dig +short example.com @${r} | head -n 5; done
dig +short example.com CNAME @1.1.1.1 | head -n 5
dig example.com @1.1.1.1 | grep -iE "QUERY TIME|SERVER|WHEN" | head -n 5
```
Expected: `example.com` のAが各リゾルバで返る (CDNドメインでなければ一致しやすい。CDN系で差が出たらそれ自体が実例として価値がある)。

禁止: ループの回数を増やす、短間隔連打、対象ドメインの列挙スキャン。

- [ ] **Step 3: 実測表をレポートに転記する**

転記フォーマット (値を置き換えて貼る):
```markdown
### 実測 (2026-11-07, 手元)
| resolver | command | result | TTL/備考 |
|---|---|---|---|
| system-default (172.20.10.1) | `dig +short example.com` | (実測値を貼る) | (WHEN/TTLを貼る) |
| 1.1.1.1 | `dig +short example.com @1.1.1.1` | (実測値を貼る) | |
| 8.8.8.8 | `dig +short example.com @8.8.8.8` | (実測値を貼る) | |
| 9.9.9.9 | `dig +short example.com @9.9.9.9` | (実測値を貼る) | フィルタ前提のリゾルバ |
```

- [ ] **Step 4: 確認してコミットする**

```bash
grep -n "system-default" docs/research/2026-11-07-dns-resolution.md
git add docs/research/2026-11-07-dns-resolution.md
git commit -m "docs: add 4-resolver dig comparison"
```
Expected: `grep` がヒットする。

---

### Task 4: 可視境界まとめと Sources 整備

**Files:**
- Modify: `docs/research/2026-11-07-dns-resolution.md` (Section 3 + Sources)
- Test: `grep -n "Sources" docs/research/2026-11-07-dns-resolution.md`

- [ ] **Step 1: Section 3 を確定文で埋める**

```markdown
## 3. 可視境界まとめ
- 外から見える: パブリックゾーンのA/AAAA/CNAME、CloudFront等のエッジIPのwhois/ASN、HTTPヘッダ署名、TLS証明書のissuer/SAN。
- 外から見えない: プライベートホストゾーンの中身、VPC内リゾルバ限定の名前、Latticeサービス名 (関連付けVPCのみ)、CDNオリジン内訳。
- Route 53エイリアス (apex等) はCNAMEに出ない。CNAME不在は「CDNでない」の証拠にならない。
```

- [ ] **Step 2: Sources を日付付きで列挙する**

```markdown
## Sources
- AWS VPC DNS: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-dns.html (2026-11-07取得)
- Route 53 Resolver: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html (2026-11-07取得)
- Private hosted zones: https://docs.aws.amazon.com/route53/latest/developerguide/hosted-zones-private.html (2026-11-07取得)
- 手元実測: scutil + dig (2026-11-07, resolver 4種)
```

取得日は実際に開いた日に置き換える。開けなかったURLは書かない (欠落のまま残さない。書けるものだけ書く)。

- [ ] **Step 3: 確認してコミットする**

```bash
grep -n "Sources" docs/research/2026-11-07-dns-resolution.md
git add docs/research/2026-11-07-dns-resolution.md
git commit -m "docs: finalize visibility boundary and sources"
```
Expected: PASS。

---

### Task 5: SKILL.md §3 改訂

**Files:**
- Modify: `SKILL.md:55-61` (Resolve DNS セクション)
- Test: `grep -n "@1.1.1.1\|Resolver" SKILL.md`

- [ ] **Step 1: リゾルバ確認ステップを §3 冒頭に追加する**

現行 (55-59行付近):
```bash
dig +short <host>          # A / AAAA
dig +short <host> CNAME
```

改訂後 (この文面に置き換える):
```markdown
### 3. Resolve DNS (resolver-aware)

First, record your own resolver (`scutil --dns` on macOS, `/etc/resolv.conf`, or `systemd-resolve --status` on Linux).
Then resolve explicitly:

```bash
dig +short <host>                  # A / AAAA via system-default (record which resolver this was)
dig +short <host> @1.1.1.1         # Cloudflare
dig +short <host> @8.8.8.8         # Google
dig +short <host> CNAME @1.1.1.1
```

Record the resolver, timestamp, TTL, and whether CNAME was absent for every row in the Evidence table.
```

- [ ] **Step 2: Pitfalls に3行追記する**

`## Pitfalls` 末尾に追記 (番号は既存の次から):
```markdown
11. **Resolver matters**: the same name can return different answers via system-default vs 1.1.1.1 vs 8.8.8.8 (cache / ECS / filtering). Always record `@resolver`.
12. **Route 53 Alias hides CNAME**: apex ALIAS records return direct A records. Absence of CNAME is not evidence of no CDN.
13. **Private names are invisible from outside**: private hosted zones and VPC Lattice names only resolve from associated VPCs. Do not conclude absence from public dig.
```

- [ ] **Step 3: 報告雛形に Resolver 列を追加する**

現行:
```markdown
| Observation | Result | Suggests |
```

改訂後:
```markdown
| Observation | Resolver | Result | Suggests |
```

- [ ] **Step 4: 検証してコミットする**

```bash
grep -n "@1.1.1.1\|Resolver" SKILL.md
git add SKILL.md
git commit -m "feat: make DNS resolver explicit in skill"
```
Expected: `grep` が3件以上ヒットする。

---

### Task 6: provider-signatures.md 注記追加 (署名追加なし)

**Files:**
- Modify: `references/provider-signatures.md` (AWS章末尾)
- Test: `grep -n "解決場所\|resolver" references/provider-signatures.md`

- [ ] **Step 1: AWS章末尾に注記を足す**

`Example whois of a Tokyo-region IP...` の直後に挿入:
```markdown
**DNS visibility note**: Route 53 Alias (apex) returns direct A records with no CNAME. Private hosted zone and VPC Lattice names do not resolve from public resolvers. A `dig` result always depends on `@resolver` and where it was run (inside/outside the VPC); record both.
```

日本語版のつもりで書かず、ファイルの言語 (英語) に合わせる。署名行は追加しない。

- [ ] **Step 2: 検証してコミットする**

```bash
grep -n "visibility note" references/provider-signatures.md
git add references/provider-signatures.md
git commit -m "docs: add DNS visibility note to AWS signatures"
```
Expected: 1件ヒット。

---

### Task 7: 協力者募集 issue 雛形2件

**Files:**
- Create: `docs/research/issues/issue-lattice-draft.md`
- Create: `docs/research/issues/issue-global-resolver-draft.md`
- Test: `ls docs/research/issues/`

- [ ] **Step 1: Lattice 雛形を作成する**

```markdown
# [Help wanted] Verify VPC Lattice DNS resolution from inside a VPC

## Why
Public `dig` cannot see Lattice names. We need hands-on verification from an associated VPC.

## Repro steps (for collaborator with a VPC + Lattice service)
1. From an EC2/CloudShell inside the associated VPC: `dig <lattice-service-dns> +short`
2. From outside (public resolver `@1.1.1.1`): `dig <same-name> +short` (expect: no answer / NXDOMAIN)
3. Record: VPC ID, region, resolver used (`169.254.169.253` or VPC CIDR+2), timestamp, outputs.

## Expected
- Inside: service IPs; Outside: no private answer. Confirm and paste both outputs.

## Constraints
- Passive DNS only. Do not publish customer domain names. Redact as needed.
```

保存先: `docs/research/issues/issue-lattice-draft.md`。

- [ ] **Step 2: Global Resolver 雛形を作成する**

```markdown
# [Help wanted] Verify Route 53 Global Resolver behavior (GA 2026-03)

## Why
Global Resolver went GA in 2026-03. It is expensive to run, so maintainers cannot verify alone.

## Repro steps (only if you already run it)
1. Link the AWS What's New / Docs URL for GA (paste URL + date accessed).
2. From an associated VPC: `dig <name> @<global-resolver-endpoint> +short` with timestamp.
3. From public `@1.1.1.1` / `@8.8.8.8`: same name (expect: different or no private answer).

## Cost warning
- Do NOT create paid resources for this issue. Only verify if you already operate Global Resolver. Paste redacted outputs only.
```

保存先: `docs/research/issues/issue-global-resolver-draft.md`。

- [ ] **Step 3: 確認してコミットする**

```bash
ls docs/research/issues/
git add docs/research/issues/
git commit -m "docs: add collaborator issue drafts for Lattice and Global Resolver"
```
Expected: 2ファイルがリストされる。

---

### Task 8: 最終検証

**Files:** (変更なし、検証のみ)
- Test: 全成果物の存在確認

- [ ] **Step 1: 成果物チェックリストを通す**

```bash
ls docs/research/2026-11-07-dns-resolution.md docs/research/issues/issue-lattice-draft.md docs/research/issues/issue-global-resolver-draft.md docs/superpowers/specs/2026-11-07-dns-resolver-design.md
grep -c "Resolver" SKILL.md
grep -c "visibility note" references/provider-signatures.md
git status --short
```
Expected: `ls` が4パスを返し、`grep -c` がどちらも1以上、`git status` がclean。

- [ ] **Step 2: 不足があれば Task 1-7 に戻る。なければ報告して終了する**

追加コミットは作らない。検証のみのタスク。
```

