# DNS解決場所による見え方の違い — 調査レポート (2026-11-07)

## 0. 実行環境のリゾルバ
- system-default: 172.20.10.1 (+ link-local IPv6), `scutil --dns` で確認 (2026-11-07)

## 1. VPC内DNS基礎 (文献)

### VPCリゾルバ
- Route 53 Resolver (別名 Amazon DNS server / AmazonProvidedDNS) は各 AZ に組み込まれた再帰リゾルバで、全 VPC で既定有効。EC2 等からの DNS クエリに再帰的に応答する (パブリック名の反復解決、VPC 固有名、プライベートホストゾーン)。
- 到達先は 2 つの書き方: リンクローカル `169.254.169.253` (IPv4、IPv6 は `fd00:ec2::253`) と `VPC CIDR + 2` (例: VPC が `10.0.0.0/16` なら `10.0.0.2`)。VPC 内リソースはリンクローカル経由で問い合わせ、クエリは VPC 内で Resolver にプライベート転送されネットワーク上に見えない。
- 前提属性: `enableDnsSupport` / `enableDnsHostnames`。プライベートホストゾーンや PrivateLink のプライベート DNS を使う場合は両方 `true` が必須。
- 制限: Resolver が扱うのは再帰クエリのみ。セキュリティグループや NACL で Resolver との通信をフィルタできない。

### プライベートホストゾーン / Resolver Endpoint / DNS Firewall
- プライベートホストゾーンは 1 つ以上の VPC に関連付けられたドメインの応答定義。関連付け VPC 内の EC2 (またはハイブリッド構成の Inbound Endpoint 経由) からのクエリにのみ応答する。
- 外部 (関連付けのない場所) から同名を `dig` してもプライベート情報は返らない。NS レコードはインターネット上可視の予約名だが、直接問い合わせてもゾーン内容は得られず、VPC とホストゾーンの関連付けに基づき Resolver がプライベート接続で解決する。
- Resolver Endpoint: Outbound は VPC → オンプレ等への条件付き転送 (Resolver ルールでドメインごとに転送先を指定、VPN/DX 経由)。Inbound はオンプレ等 → VPC 内名の解決。これらがハイブリッド DNS の境界になる。
- DNS Firewall は VPC からの外向き DNS クエリをフィルタしうる (許可/拒否リストによるドメイン制御)。詳細なルール意味論の調査は本レポートの範囲外とし、ここでは「外向き解決の途中で遮断・改変されうる境界」として記録する。

## 2. パブリックDNS組み合わせ (文献+実測)
### 文献要点
- `1.1.1.1` (Cloudflare)、`8.8.8.8` (Google)、`9.9.9.9` (Quad9) はキャッシュ・ECS・フィルタ方針が異なるため、CDNのGeo回答は食い違うことがある。
- `dig` でリゾルバを省略すると system-default (本環境では 172.20.10.1) を見ていることになり、再現性が落ちる。`@resolver` 明示が必須。

## 3. 可視境界まとめ
- 外から見える: パブリックゾーン、CNAME/A、エッジIPのwhois/ASN。
- 外から見えない: プライベートゾーン、Lattice名 (関連付けVPCのみ)、オリジン内訳。

## Sources
- Amazon VPC User Guide — DNS attributes for your VPC (https://docs.aws.amazon.com/vpc/latest/userguide/vpc-dns.html, 取得日 2026-11-07)
- Amazon VPC User Guide — Understanding Amazon DNS (https://docs.aws.amazon.com/vpc/latest/userguide/AmazonDNS-concepts.html, 取得日 2026-11-07)
- Amazon Route 53 Developer Guide — What is Route 53 VPC Resolver? (https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html, 取得日 2026-11-07)
- Amazon Route 53 Developer Guide — Working with private hosted zones (https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html, 取得日 2026-11-07。旧小文字 URL `route53/.../hosted-zones-private.html` は 404 のため正規の大文字パスで取得)
