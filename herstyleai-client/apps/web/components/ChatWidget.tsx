"use client";

import { useState } from "react";
import Link from "next/link";
import { Icon } from "./Icon";

export function ChatWidget() {
  const [open, setOpen] = useState(false);
  return (
    <>
      {open && (
        <div className="chat-widget-panel">
          <div className="chat-widget-head">
            <div><span className="brand-mark small">H</span><strong>HerStyle AI</strong></div>
            <button className="icon-btn" onClick={() => setOpen(false)}>×</button>
          </div>
          <div className="quick-prompts">
            <button><Icon name="sparkle" size={18}/> Gợi ý phối đồ</button>
            <button><Icon name="shirt" size={18}/> Phân tích trang phục</button>
            <button><Icon name="calendar" size={18}/> Lên lịch phối đồ</button>
          </div>
          <div className="mini-message">Hôm nay bạn muốn mặc theo phong cách nào?</div>
          <Link href="/chat" className="mini-chat-input">Hỏi HerStyle AI bất cứ điều gì… <Icon name="send" size={16}/></Link>
        </div>
      )}
      <button className="chat-fab" onClick={() => setOpen(!open)} aria-label="Mở chat AI"><Icon name="chat" size={24}/></button>
    </>
  );
}
