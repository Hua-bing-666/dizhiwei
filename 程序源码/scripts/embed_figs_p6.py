# -*- coding: utf-8 -*-
"""P6 申报书内嵌图重嵌：image6（图3-5 引脚图，改灰阶）、image8（图3-7 microSD，修正 Micro）、
image14（图8-2 二维边界，去"图C"并修正横轴为秒）。

策略：仅替换 word/media 字节，保留各图 wp:extent / a:ext 不变（版面零位移）。
备份落 tmp/；ZIP_DEFLATED 重写 + testzip 完整性校验 + os.replace 原子落盘。
"""
import zipfile, os, shutil, struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "大创申报书_正式稿6.docx")
BAK = os.path.join(ROOT, "tmp", "申报书_备份_P6_图3-5图3-7图8-2重嵌前.docx")
TMP = os.path.join(ROOT, "tmp", "申报书_P6_rebuild.docx")

JOBS = [
    ("word/media/image6.png", "application/figures/图3-5_SN74LVC1G17引脚图_灰阶.png"),
    ("word/media/image8.png", "application/figures/图3-7_microSD模块原理图.png"),
    ("word/media/image14.png", "simulation/project_review/figures/detection_boundary.png"),
]


def png_dims(p):
    with open(p, "rb") as f:
        f.read(16)
        return struct.unpack(">II", f.read(8))


def main():
    os.makedirs(os.path.dirname(BAK), exist_ok=True)
    if not os.path.exists(BAK):
        shutil.copy(SRC, BAK)
        print("备份 ->", BAK)

    z = zipfile.ZipFile(SRC)
    names = z.namelist()
    data = {n: z.read(n) for n in names}
    z.close()

    for media, newp in JOBS:
        assert media in names, f"{media} 不在 docx"
        full = os.path.join(ROOT, newp)
        assert os.path.exists(full), f"新图缺失: {full}"
        w, h = png_dims(full)
        data[media] = open(full, "rb").read()
        print(f"  替换 {media} <- {os.path.basename(newp)} ({w}x{h}, {len(data[media])} B)")

    if os.path.exists(TMP):
        os.remove(TMP)
    with zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, data[n])
        err = z.testzip()
    assert err is None, f"zip 完整性失败: {err}"

    os.replace(TMP, SRC)
    print("已落盘", SRC)


if __name__ == "__main__":
    main()
