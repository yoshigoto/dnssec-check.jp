# DNSSEC検証用ページ

DNSSECの検証結果を確認するための静的なWebサイトです。

- 日本語版: <https://www.dnssec-check.jp/>
- 英語版: <https://www.dnssec-check.jp/en/>

## 掲載内容

[index.html](index.html) には、DNSSECの検証用ドメインと、検証ツールへのリンクを掲載しています。各リンクから対象ドメインを検証できます。

委任の検証では、次の署名アルゴリズムごとに成功例と失敗例を確認できます。

- RSASHA256
- ECDSAP256SHA256
- ED25519
- ED448
- ML-DSA-44（ドメイン名の識別子: `mldsa44`）

失敗例には、親ゾーンのDSと子ゾーンのDNSKEYの不一致、DSまたはDNSKEY RRsetの署名破損、DNSKEY RRset署名の期限切れがあります。A RRset署名の破損例は、委任の検証とは別の表にまとめています。

NSECとNSEC3の表では、NXDOMAINの不在証明やNODATAの型ビットマップの不整合を確認できます。NSEC3では反復回数やsaltの異なる例と、Opt-OutによるDS不在証明の例も掲載しています。これらの不在証明の検証例はRSASHA256を使用します。

[dnssec-negative-answers.html](dnssec-negative-answers.html) では、DNSの否定応答、NSEC/NSEC3の順序と範囲、Closest EncloserとNext Closer Name、Opt-Outの概要を説明しています。

検証用ドメインには、意図的にDNSSECの不整合を作ったものが含まれます。失敗例では検証エラーが期待される結果です。

## ドメイン名の構成

基本的な形式は `<検証ケース>.<アルゴリズム>.dnssec-check.jp` です。たとえば、`success.rsasha256.dnssec-check.jp` はRSASHA256の成功例です。A RRset署名の破損例は `corrupted.sign.a.error.<アルゴリズム>.dnssec-check.jp` の形式です。

NSEC/NSEC3の検証ケースでは、方式や不整合の種類を名前に含めます。NSEC3では、反復回数とsaltの設定も名前で区別します。例: `missing.cover.mismatch.nsec3.iter0.nosalt.rsasha256.dnssec-check.jp`。

検証用ドメインの構成には、[dnssec-corrupt-zone](https://github.com/yoshigoto/dnssec-corrupt-zone) のゾーンテンプレートを使用しています。掲載するドメイン名や検証ケースを変更する場合は、対応するテンプレートも確認してください。

## ローカルで確認する

リポジトリのルートで、Python 3の静的HTTPサーバーを起動します。

```bash
python3 -m http.server 8000
```

次のURLをブラウザーで開きます。

- 日本語版トップページ: <http://127.0.0.1:8000/>
- 英語版トップページ: <http://127.0.0.1:8000/en/>
- 日本語版の解説: <http://127.0.0.1:8000/dnssec-negative-answers.html>
- 英語版の解説: <http://127.0.0.1:8000/en/dnssec-negative-answers.html>

VS Codeでは、コマンドパレットから `Tasks: Run Task` → `Serve static HTML` を選んでも起動できます。確認後は、サーバーを起動したターミナルで `Ctrl+C` を押して終了してください。

## テスト

Python 3の標準ライブラリだけで実行できます。追加のパッケージは不要です。

```bash
python3 -m unittest -v
```

テストでは、検証用ドメイン名とリンク先の整合性、日英ページの対応、言語設定、ページ内リンク、見出しや本文の基本構造などを確認します。DNSへの問い合わせや、掲載ドメインの実際の検証結果はテストしません。

## ファイル構成

- [index.html](index.html): 日本語版の検証用リンク一覧
- [en/index.html](en/index.html): 英語版の検証用リンク一覧
- [dnssec-negative-answers.html](dnssec-negative-answers.html): 日本語版のNSEC/NSEC3解説
- [en/dnssec-negative-answers.html](en/dnssec-negative-answers.html): 英語版のNSEC/NSEC3解説
- [test_domains.py](test_domains.py): 検証用ドメイン名とリンクの整合性テスト
- [test_localization.py](test_localization.py): 言語設定、ページ構造、翻訳間の整合性テスト
