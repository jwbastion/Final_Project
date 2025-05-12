declare module 'html2pdf.js' {
  interface Html2PdfOptions {
    margin?: number | number[];
    filename?: string;
    image?: { type: string; quality: number };
    html2canvas?: object;
    jsPDF?: { unit: string; format: string; orientation: string };
  }

  interface Html2Pdf {
    from(element: HTMLElement): this;
    set(options: Html2PdfOptions): this;
    toPdf(): this;
    get(type: 'blob' | 'datauristring' | 'arraybuffer'): Promise<Blob | string | ArrayBuffer>;
    output(type: 'blob' | 'datauristring' | 'arraybuffer'): Promise<Blob | string | ArrayBuffer>;
    save(filename?: string): void;
  }

  const html2pdf: () => Html2Pdf;
  export default html2pdf;
}
