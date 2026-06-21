import uvicorn

from .config import DVA_VC_HOST, DVA_VC_PORT


def main():
    uvicorn.run(
        "dva_vc_issuer.app:app",
        host=DVA_VC_HOST,
        port=DVA_VC_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()