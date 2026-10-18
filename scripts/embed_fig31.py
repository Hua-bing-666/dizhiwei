"""P5 图3-1 重嵌：把新绘制的 图3-1_系统总体结构.png 写入 media/image2.png，
并同步更新 rId7 绘图块的 wp:extent / a:ext 到新图比例，避免拉伸变形。

OOXML 级替换（同 图3-2 / 图3-8 已验证做法）：
  - 读全部 parts → 换 image2.png 字节 → 改 wp:extent / a:ext → ZIP_DEFLATED 重写 → testzip → os.replace
  - 备份落 tmp/

比例计算：新 PNG 1931x1188 (ratio=1.6254)；保留旧帧宽 14.817cm(5334000 EMU)，
          高 = round(5334000 / 1.6254) = 3281317 EMU。
"""
import zipfile, re, shutil, os, struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "大创申报书_正式稿6.docx")
BAK = os.path.join(ROOT, "tmp", "申报书_备份_P5图3-1重嵌前.docx")
TMP = os.path.join(ROOT, "tmp", "申报书_P5图3-1_rebuild.docx")
NEW_PNG = os.path.join(ROOT, "deliverables", "图3-1_系统总体结构.png")
MEDIA = "word/media/image2.png"
RID = "rId7"


def png_dims(p):
    with open(p, "rb") as f:
        f.read(16)
        w, h = struct.unpack(">II", f.read(8))
    return w, h


def main():
    os.makedirs(os.path.dirname(BAK), exist_ok=True)
    if not os.path.exists(BAK):
        shutil.copy(SRC, BAK)

    w, h = png_dims(NEW_PNG)
    ratio = w / h
    CX = 5334000            # 保留旧帧宽 14.817cm
    CY = round(CX / ratio)  # 按新图比例重算高
    print(f"新图 {w}x{h} ratio={ratio:.6f} -> cx={CX} cy={CY}")

    new_bytes = open(NEW_PNG, "rb").read()

    z = zipfile.ZipFile(SRC)
    names = z.namelist()
    assert MEDIA in names, f"{MEDIA} 不在 {SRC}"
    data = {n: z.read(n) for n in names}
    z.close()

    # 仅 rId7 指向 image2.png（rel 校验）
    rels = data["word/_rels/document.xml.rels"].decode("utf8")
    refs = re.findall(r'Id="([^"]+)"[^>]*Target="media/image2.png"', rels)
    assert refs == [RID], f"image2.png 引用异常: {refs}"

    # 替换媒体字节
    data[MEDIA] = new_bytes

    # 在 rId7 绘图块内替换 extent
    doc = data["word/document.xml"].decode("utf8")
    i = doc.find(f'r:embed="{RID}"')
    assert i > 0, "rId7 未在 document.xml 找到"
    start = doc.rfind("<wp:extent", 0, i)
    end = doc.find("</wp:inline>", i)
    assert start > 0 and end > 0, "未定位 rId7 绘图块"
    region = doc[start:end]
    region2 = re.sub(r'<wp:extent cx="\d+" cy="\d+"', f'<wp:extent cx="{CX}" cy="{CY}"', region)
    region2 = re.sub(r'<a:ext cx="\d+" cy="\d+"', f'<a:ext cx="{CX}" cy="{CY}"', region2)
    assert region2 != region, "wp:extent / a:ext 未替换"
    doc = doc[:start] + region2 + doc[end:]
    data["word/document.xml"] = doc.encode("utf8")

    # 重写 zip 并校验完整性
    if os.path.exists(TMP):
        os.remove(TMP)
    with zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, data[n])
        err = z.testzip()
    assert err is None, f"zip 完整性失败: {err}"

    os.replace(TMP, SRC)
    print(f"已落盘 {SRC}；备份 {BAK}")
    print(f"image2.png 新字节数 {len(new_bytes)}；帧 {CX}x{CY} (EMU)")


if __name__ == "__main__":
    main()
