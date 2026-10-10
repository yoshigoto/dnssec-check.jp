# DNSSEC信頼の連鎖確認ページ

DNSSECの信頼の連鎖（Chain of Trust）の検証結果を確認するためのテストページです。

公開URL: https://www.dnssec-check.jp/

## 概要

このページには、DNSSECの署名アルゴリズムごとに、検証が成功するパターンおよび様々な理由で検証が失敗するパターンのドメイン名がまとめられています。各リンクをクリックすると、[DNSSEC委任状態検証ツール](https://www.on-link.jp/dnssec-validator/)の画面に遷移し、対象ドメインのDNSSEC検証結果を確認できます。

対応している署名アルゴリズムは以下の4種類です。

- RSASHA256
- ECDSAP256SHA256
- ED25519
- ED448

このリポジトリでは、テストページの index.html と、NSEC/NSEC3による否定応答の解説ページをバージョン管理しています。

## 開発環境

WSL2 の Ubuntu で開発・確認します。以下のコマンドが利用できる環境を前提としています。

- Git
- Python 3
- curl

リポジトリを WSL2 の Ubuntu 側に配置して、Ubuntu のターミナルから操作してください。

### ローカルで確認する

リポジトリのルートディレクトリで静的 HTTP サーバーを起動します。

```bash
python3 -m http.server 8000
```

ブラウザーで http://127.0.0.1:8000/index.html を開いてページを確認します。VS Code のコマンドパレットから `Tasks: Run Task` を実行し、`Serve static HTML` を選択して起動することもできます。

別の Ubuntu ターミナルでは、次のコマンドで HTTP 応答とページ内容を確認できます。

```bash
curl -I http://127.0.0.1:8000/index.html
curl -fsS http://127.0.0.1:8000/index.html | grep -q '<title>'
```

確認が終わったら、HTTP サーバーを起動したターミナルで `Ctrl+C` を押して終了します。

## 確認できるパターン

各アルゴリズムの委任状態について、以下のパターンを確認できます。

| パターン | 内容 |
| --- | --- |
| 成功パターン (DNSSEC総合検証成功) | DNSSECの検証が正しく成功する |
| 失敗パターン：親DSのKey Tagと子DNSKEYのKey Tagが不一致 | DSレコードのKey Tagが一致せず検証に失敗する |
| 失敗パターン：親DSのDigestと子DNSKEYから計算したDigestが不一致 | DSレコードのハッシュ値（Digest）が一致せず検証に失敗する |
| 失敗パターン：親ゾーンのDS RRset署名（RRSIG）破損 | 親ゾーン（.jp）のDS RRset署名検証に失敗する |
| 失敗パターン：DNSKEY RRset署名（RRSIG）破損 | 子ゾーンのDNSKEY RRsetの署名検証に失敗する |
| 失敗パターン：DNSKEY RRsetのRRSIG期限切れ | 子ゾーンのDNSKEY RRsetに対する署名の有効期限切れにより検証に失敗する |
| 失敗パターン：A RRset署名（RRSIG）破損 | Aリソースレコードの署名検証に失敗する。委任状態の検証とは目的が異なるため、独立した表で確認する |
| 失敗パターン：不在証明のカバー不成立 (NSEC) | NSECの Next Domain Name が対象名を正しくカバーせず、NXDOMAIN の証明に失敗する |
| 失敗パターン：NODATA不在証明の不整合 (NSEC) | NSEC の型ビットマップと実際の応答が不一致で、NODATA の証明が破綻する。A・MX・TXT問い合わせ型を確認する |
| 失敗パターン：不在証明のカバー不成立 (NSEC3) | NSEC3 の Next Hashed Owner Name が対象名を正しくカバーせず、NXDOMAIN の証明に失敗する。反復回数とsalt設定ごとに確認する |
| 失敗パターン：NODATA不在証明の不整合 (NSEC3) | NSEC3 の型ビットマップと実際の応答が不一致で、NODATA の証明が破綻する。MX・TXT問い合わせ型と異なる反復回数・saltを確認する |
| 失敗パターン：Opt-Out 不在証明のカバー不成立 (NSEC3) | DNSSECで保護されない指定名 `unsigned` を覆う Opt-Out フラグ付き NSEC3 のカバー範囲が壊れており、不在証明の検証に失敗する |

ドメイン名は `<パターン>.<アルゴリズム>.dnssec-check.jp` の形式で構成されています（例：`success.rsasha256.dnssec-check.jp`）。
NSEC や NSEC3 のケースでは、対象名や不整合の種類を名前に含めています。例として、NSEC のカバー不成立は `missing.cover.mismatch.nsec.rsasha256.dnssec-check.jp`、NSEC3 のカバー不成立は `missing.cover.mismatch.nsec3.iter0.nosalt.rsasha256.dnssec-check.jp` のように命名しています。
Opt-Out NSEC3 のカバー不成立ケースは、反復回数とsalt設定を含む `unsigned.optout.mismatch.nsec3.iter<回数>.<salt設定>.rsasha256.dnssec-check.jp` の形式です（例：`unsigned.optout.mismatch.nsec3.iter0.nosalt.rsasha256.dnssec-check.jp`）。
NSEC と NSEC3 の型ビットマップ不整合は MX・TXT 問い合わせ型にも対応し、たとえば `target.type.mx.mismatch.nsec.rsasha256.dnssec-check.jp` や `target.type.txt.mismatch.nsec3.iter0.nosalt.rsasha256.dnssec-check.jp` を確認できます。NSEC3 のカバー不成立、型ビットマップ不整合、Opt-Out カバー不成立には、反復回数 0・salt なし、反復回数 0・salt `A1B2`、反復回数 1・salt なし、反復回数 1・salt `A1B2` の各ドメインがあります。
NSEC および NSEC3 の不在証明検証は、RSASHA256 のドメインで確認します。

Aリソースレコードの署名検証では、`corrupted.sign.a.error.<アルゴリズム>.dnssec-check.jp` の形式で命名しています。これらは `www.` を付けた委任状態確認用ドメインとは別の目的で使用します。

## ファイル構成

- [index.html](index.html) - 確認用リンク一覧を掲載したページ本体
- [dnssec-negative-answers.html](dnssec-negative-answers.html) - DNSSECの否定応答、NSEC/NSEC3の順序、Closest EncloserとNext Closer Nameの解説
- [test_domains.py](test_domains.py) - ドメイン名とリンク表示の整合性を確認するテスト

## 検証用のドメイン名について

検証用のドメイン名を作成する際は [dnssec-corrupt-zone](https://github.com/yoshigoto/dnssec-corrupt-zone) を用いています。掲載するドメイン名は [アルゴリズム別ゾーンテンプレート](https://github.com/yoshigoto/dnssec-corrupt-zone/blob/main/templates/template.algorithm.dnssec-check.jp.zone) と [Opt-Out用ゾーンテンプレート](https://github.com/yoshigoto/dnssec-corrupt-zone/blob/main/templates/template.optout.algorithm.dnssec-check.jp.zone) のレコード名を含めています。
このツールでは、DS や DNSKEY の破損に加えて、NSEC / NSEC3 の不在証明や型ビットマップの破損を意図的に作成できます。`corrupted`、`missing`、`target` などは各ゾーン内で定義されたレコード名であり、検証用ドメイン名の先頭に保持します。Opt-Out NSEC3 のケースは `nsec3-optout-cover-mismatch` モードで作成し、未署名委任名 `unsigned` も完全な検証用ドメイン名に含めています。
そのため、ドメイン名の命名規則には、失敗パターンの種類と対象の署名アルゴリズムが反映されており、たとえば `missing.cover.mismatch.nsec.rsasha256.dnssec-check.jp` などの形式で管理しています。
