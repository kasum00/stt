import Icon from "./Icon";

export const products = [
  {name:"Navy Office Blazer",category:"Áo khoác",img:"/assets/blazer.png"},
  {name:"White Office Shirt",category:"Áo",img:"/assets/shirt-white.png"},
  {name:"Blue Straight Jeans",category:"Quần",img:"/assets/jeans-blue.png"},
  {name:"Beige Office Blazer",category:"Áo khoác",img:"/assets/blazer-beige.png"},
  {name:"Black Trousers",category:"Quần",img:"/assets/pants-black.png"},
  {name:"Black Heels",category:"Giày",img:"/assets/heels.png"},
];

export default function ProductCard({item,compact=false}:{item:(typeof products)[number],compact?:boolean}) {
  return (
    <article className={`product-card ${compact?"compact":""}`}>
      {!compact && <button className="product-heart"><Icon name="heart" size={16}/></button>}
      <div className="product-image"><img src={item.img} alt={item.name}/></div>
      {!compact && <div className="product-meta"><strong>{item.name}</strong><span>{item.category}</span></div>}
    </article>
  );
}