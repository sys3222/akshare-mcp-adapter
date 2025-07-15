import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['dev', 'prod'], help='运行模式')
    args = parser.parse_args()

    if args.mode == 'dev':
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=12001,
            reload=True,
            workers=1
        )
    else:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=12001,
            workers=4,
            log_level="info"
        )
