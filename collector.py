#!/usr/bin/env python3
"""Warman Quant public-data collector. Research data, not an order generator."""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import yfinance as yf

SYMBOLS = {
    'OMXS30':'^OMX', 'DAX':'^GDAXI', 'SP500':'^GSPC', 'NASDAQ100':'^NDX',
    'GOLD_FUT':'GC=F', 'SILVER_FUT':'SI=F', 'WTI_FUT':'CL=F', 'BRENT_FUT':'BZ=F',
    'US30Y_BOND_FUT':'ZB=F', 'US10Y_NOTE_FUT':'ZN=F', 'US30Y_YIELD':'^TYX', 'US10Y_YIELD':'^TNX',
    'VIX':'^VIX', 'OVX':'^OVX', 'GVZ':'^GVZ',
    'EURUSD':'EURUSD=X', 'USDSEK':'SEK=X', 'INVESTOR_B':'INVE-B.ST',
    'VOLVO_B':'VOLV-B.ST', 'ATLAS_A':'ATCO-A.ST', 'ABB':'ABB.ST',
    'NVIDIA':'NVDA', 'MICROSOFT':'MSFT', 'APPLE':'AAPL', 'TESLA':'TSLA',
    'AMAZON':'AMZN', 'META':'META', 'BITCOIN':'BTC-USD', 'ETHEREUM':'ETH-USD', 'SOLANA':'SOL-USD',
}
REQUIRED = ['Open','High','Low','Close','Volume']

def get_series(ticker, interval, period, out=None, name=None):
    raw = yf.download(ticker, interval=interval, period=period, auto_adjust=False,
                      progress=False, threads=False, prepost=False, timeout=18)
    if raw is None or raw.empty:
        raise ValueError('empty response')
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    missing = [c for c in REQUIRED if c not in raw.columns]
    if missing: raise ValueError(f'missing columns: {missing}')
    df = raw[REQUIRED].copy().sort_index()
    df = df[~df.index.duplicated(keep='last')]
    if interval == '1d':
        # Daily bars represent exchange session dates, not UTC instants.
        df.index = pd.to_datetime(df.index.date).tz_localize(timezone.utc)
    else:
        if df.index.tz is None: raise ValueError('intraday timestamps lack timezone')
        df.index = df.index.tz_convert(timezone.utc)
    numeric = df[REQUIRED].apply(pd.to_numeric, errors='coerce')
    df = numeric.dropna(subset=['Open','High','Low','Close'])
    if df.empty: raise ValueError('no valid OHLC rows')
    invalid = (df.High < df[['Open','Low','Close']].max(axis=1)) | (df.Low > df[['Open','High','Close']].min(axis=1)) | (df.Low <= 0)
    if invalid.any():
        # Preserve rejected source rows for audit; never silently repair OHLC.
        if out is not None and name is not None:
            rejected=df.loc[invalid].copy()
            rejected.insert(0,'source_date',rejected.index.strftime('%Y-%m-%dT%H:%M:%SZ'))
            rejected.to_csv(out/f'{name}_{interval}_rejected.csv',index=False)
        df=df.loc[~invalid].copy()
        if df.empty: raise ValueError('all OHLC rows invalid')
    df['Volume'] = df.Volume.fillna(0)
    df['timestamp_utc'] = df.index.strftime('%Y-%m-%dT%H:%M:%SZ')
    if interval == '1d': df['session_date'] = df.index.strftime('%Y-%m-%d')
    return df

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='output')
    parser.add_argument('--symbols',nargs='*',default=list(SYMBOLS))
    parser.add_argument('--sleep',type=float,default=0.35)
    args=parser.parse_args()
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc)
    manifest={'generated_at_utc':now.isoformat(),'source':'Yahoo Finance via yfinance (unofficial)',
              'warning':'Research-only data. Verify licensing, market hours, timestamps and executable quotes before trading.',
              'symbols':{},'errors':{}}
    for name in args.symbols:
        ticker=SYMBOLS.get(name,name)
        result={}
        for interval,period in [('1h','60d'),('1d','10y')]:
            try:
                df=get_series(ticker,interval,period,out,name)
                filename=f'{name.replace("/","_")}_{interval}.csv'
                cols=(['session_date','timestamp_utc'] if interval=='1d' else ['timestamp_utc'])+REQUIRED
                df[cols].to_csv(out/filename,index=False)
                last=df.index[-1].to_pydatetime()
                result[interval]={'file':filename,'rows':len(df),'last_bar_timestamp_utc':last.isoformat(),
                                  'age_hours_at_export':round((now-last).total_seconds()/3600,2),
                                  'volume_nonzero_rows':int((df.Volume>0).sum()),
                                  'timestamp_semantics':('session_date' if interval=='1d' else 'bar_start_utc'),
                                  'last_bar_provisional':bool(
                                      (interval=='1h' and last >= now.replace(minute=0,second=0,microsecond=0))
                                      or (interval=='1d' and last.date()==now.date())),
                                  'rejected_rows_file':(f'{name}_{interval}_rejected.csv' if (out/f'{name}_{interval}_rejected.csv').exists() else None),
                                  'note':'Index volume may be zero/unavailable; never infer exchange traded volume.'}
                print(f'OK {name:14} {interval:3} {len(df):5} rows | last {last.isoformat()}')
            except Exception as exc:
                manifest['errors'][f'{name}/{interval}']=str(exc)
                print(f'FAIL {name} {interval}: {exc}',file=sys.stderr)
            time.sleep(args.sleep)
        if result: manifest['symbols'][name]={'ticker':ticker,**result}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print()
    print(f'Files in: {out.resolve()}')
    print(f'Successful instruments: {len(manifest["symbols"])}; failed downloads: {len(manifest["errors"])}')
    if not manifest['symbols']: sys.exit(2)

if __name__=='__main__': main()
